"""Opt-in R2 TLS tunnel policy; no TLS termination, credentials, or default outbound sender."""

import select
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import ip_address
from threading import Event, Lock
from urllib.parse import urlsplit

DESTINATION = "sts.us-east-1.amazonaws.com:443"
MAX_DIAGNOSTICS = 16
PUBLIC_ENDPOINTS = {
    "sts.us-east-1.amazonaws.com",
    "sts.amazonaws.com",
    "sts.us-east-1.api.aws",
    "signin.us-east-1.amazonaws.com",
    "us-east-1.signin.aws.amazon.com",
    "us-east-1.signin.aws",
    "iam.amazonaws.com",
}


def classify_destination(authority):
    """Return finite labels/public constants, never arbitrary hostnames or URLs."""
    if len(authority) > 512 or any(c in authority for c in "@/?#\\ \r\n\t"):
        return {"destination_class": "malformed_authority", "port_class": "unknown"}
    try:
        parsed = urlsplit("//" + authority)
        host, port = parsed.hostname, parsed.port
        if not host or not port:
            raise ValueError
    except ValueError:
        return {"destination_class": "malformed_authority", "port_class": "unknown"}
    result = {"port_class": "https_443" if port == 443 else "other_port"}
    if host in PUBLIC_ENDPOINTS:
        result["public_endpoint"] = host
    try:
        address = ip_address(host)
    except ValueError:
        address = None
    if address:
        category = (
            "loopback_ip"
            if address.is_loopback
            else "unspecified_ip"
            if address.is_unspecified
            else "nonloopback_ip"
        )
    elif host == "localhost":
        category = "loopback_name"
    elif host == "sts.us-east-1.amazonaws.com":
        category = "regional_sts"
    elif (
        host == "sts.amazonaws.com"
        or host.startswith("sts.")
        and host.endswith((".amazonaws.com", ".api.aws"))
    ):
        category = "other_sts"
    elif ".signin." in host or host.endswith(".signin.aws"):
        category = "sign_in_or_refresh"
    elif host == "iam.amazonaws.com":
        category = "iam"
    elif host.endswith((".amazonaws.com", ".api.aws")):
        category = "other_aws_service"
    else:
        category = "other_destination"
    result["destination_class"] = category
    return result


class TunnelPolicy:
    def __init__(self, connector=None):
        self.connector = connector
        self.abort = Event()
        self.lock = Lock()
        self.attempts = 0
        self.allowed = 0
        self.blocked = []
        self.events = []
        self.transport_events = []

    def claim(self, method, destination):
        with self.lock:
            self.attempts += 1
            reason = None
            if method != "CONNECT":
                reason = "non_tls_request"
            elif destination != DESTINATION:
                reason = (
                    "login_refresh_endpoint_blocked"
                    if destination == "signin.us-east-1.amazonaws.com:443"
                    or destination.endswith(".signin.aws.amazon.com:443")
                    else "unexpected_destination"
                )
            elif self.connector is None:
                reason = "offline_no_sender"
            elif self.allowed:
                reason = "tunnel_limit_exhausted"
            if len(self.events) < MAX_DIAGNOSTICS:
                self.events.append(
                    {
                        "method_class": "connect" if method == "CONNECT" else "non_connect",
                        **classify_destination(destination),
                        "decision": "blocked" if reason else "allowed",
                        "reason": reason or "regional_sts_only",
                    }
                )
            if reason:
                if len(self.blocked) < MAX_DIAGNOSTICS:
                    self.blocked.append(reason)
                self.abort.set()
                return False
            self.allowed += 1
            return True

    def diagnostics(self):
        with self.lock:
            return {
                "events": [dict(event) for event in self.events],
                "truncated": self.attempts > len(self.events),
                "maximum_events": MAX_DIAGNOSTICS,
                "transport_events": list(self.transport_events),
            }

    def transport_error(self, error):
        # A peer may reset its TLS socket after a successful request. This is
        # transport closure, never evidence of authentication success or failure.
        closed = isinstance(error, (ConnectionResetError, BrokenPipeError))
        kind = (
            "peer_closed"
            if closed
            else "timeout"
            if isinstance(error, TimeoutError)
            else "byte_limit"
            if isinstance(error, ValueError)
            else "connection_error"
        )
        with self.lock:
            if len(self.transport_events) < MAX_DIAGNOSTICS:
                self.transport_events.append(kind)
            if not closed:
                self.abort.set()
                if len(self.blocked) < MAX_DIAGNOSTICS:
                    self.blocked.append("transport_interrupted_or_bounded")

    def summary(self):
        with self.lock:
            return {
                "connection_attempts": self.attempts,
                "allowed_tunnels": self.allowed,
                "blocked_reasons": list(self.blocked),
            }


def server(policy):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *args):
            pass

        def do_GET(self):
            policy.claim("GET", "")
            self.send_error(403)

        do_POST = do_GET

        def do_CONNECT(self):
            if not policy.claim("CONNECT", self.path):
                self.send_error(403)
                return
            try:
                # The connector is supplied only by the separately authorized operator.
                with policy.connector() as upstream:
                    self.send_response(200, "Connection Established")
                    self.end_headers()
                    end = time.monotonic() + 25
                    remaining = 1024 * 1024
                    while not policy.abort.is_set():
                        delay = end - time.monotonic()
                        if delay <= 0:
                            raise TimeoutError
                        ready, _, _ = select.select(
                            [self.connection, upstream], [], [], min(delay, 0.25)
                        )
                        for source in ready:
                            data = source.recv(min(65536, remaining + 1))
                            if not data:
                                return
                            remaining -= len(data)
                            if remaining < 0:
                                raise ValueError("tunnel_byte_limit")
                            target = upstream if source is self.connection else self.connection
                            target.sendall(data)
            except (OSError, ValueError) as error:
                policy.transport_error(error)

    value = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    value.timeout = 5
    return value
