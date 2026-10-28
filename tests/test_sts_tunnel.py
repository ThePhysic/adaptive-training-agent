"""Only loopback/synthetic sockets. No real STS sender or credentials in these tests."""

import importlib.util
import socket
from pathlib import Path
from threading import Thread

import pytest

PATH = Path(__file__).resolve().parents[1] / "infra/aws/fixtures/sts_tunnel.py"


def tunnel():
    spec = importlib.util.spec_from_file_location("sts_tunnel", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "method,destination",
    [
        ("GET", "sts.us-east-1.amazonaws.com:443"),
        ("CONNECT", "iam.amazonaws.com:443"),
        ("CONNECT", "signin.us-east-1.amazonaws.com:443"),
        ("CONNECT", "sts.amazonaws.com:443"),
        ("CONNECT", "sts.us-east-1.amazonaws.com:80"),
        ("CONNECT", "STS.us-east-1.amazonaws.com:443"),
    ],
)
def test_unapproved_route_never_calls_sender(method, destination):
    module = tunnel()
    policy = module.TunnelPolicy(lambda: pytest.fail("Must not send"))
    assert not policy.claim(method, destination) and policy.abort.is_set()
    assert policy.allowed == 0


def test_no_default_sender_or_second_connection():
    module = tunnel()
    assert not module.TunnelPolicy().claim("CONNECT", module.DESTINATION)
    policy = module.TunnelPolicy(lambda: None)
    assert policy.claim("CONNECT", module.DESTINATION)
    assert not policy.claim("CONNECT", module.DESTINATION)
    assert policy.summary()["blocked_reasons"] == ["tunnel_limit_exhausted"]


def test_refresh_hostname_variant_is_classified_and_remains_blocked():
    module = tunnel()
    policy = module.TunnelPolicy(lambda: pytest.fail("No refresh permitted"))
    assert not policy.claim("CONNECT", "us-east-1.signin.aws.amazon.com:443")
    assert policy.summary()["blocked_reasons"] == ["login_refresh_endpoint_blocked"]
    assert policy.allowed == 0


@pytest.mark.parametrize(
    "authority,category",
    [
        ("sts.us-east-1.amazonaws.com:443", "regional_sts"),
        ("us-east-1.signin.aws.amazon.com:443", "sign_in_or_refresh"),
        ("[::]:1234", "unspecified_ip"),
        ("127.0.0.1:4321", "loopback_ip"),
        ("iam.amazonaws.com:443", "iam"),
        ("private-account.synthetic.amazonaws.com:443", "other_aws_service"),
        ("credential-canary@private.invalid:443", "malformed_authority"),
        ("private.invalid:443/secret-canary", "malformed_authority"),
        ("x" * 513, "malformed_authority"),
    ],
)
def test_destination_diagnostics_classify_without_private_values(authority, category):
    module = tunnel()
    value = module.classify_destination(authority)
    assert value["destination_class"] == category
    if "public_endpoint" in value:
        assert value["public_endpoint"] in module.PUBLIC_ENDPOINTS
    assert "private" not in str(value) and "canary" not in str(value)


def test_diagnostics_are_bounded_and_do_not_expand_authority():
    module = tunnel()
    policy = module.TunnelPolicy(lambda: pytest.fail("Must never send"))
    for _ in range(40):
        assert not policy.claim("CONNECT", "private-secret-canary.invalid:443")
    data = policy.diagnostics()
    assert len(data["events"]) == data["maximum_events"] == 16 and data["truncated"]
    assert len(policy.summary()["blocked_reasons"]) == 16 and policy.allowed == 0
    assert "private-secret-canary" not in str(data)


@pytest.mark.parametrize("error", [ConnectionResetError, BrokenPipeError])
def test_peer_close_is_not_an_authorization_failure_or_authentication_success(error):
    module = tunnel()
    policy = module.TunnelPolicy()
    policy.transport_error(error("synthetic-secret-canary"))
    assert not policy.abort.is_set()
    assert policy.summary()["blocked_reasons"] == []
    assert policy.diagnostics()["transport_events"] == ["peer_closed"]
    assert "synthetic-secret-canary" not in str(policy.diagnostics())
    assert policy.allowed == 0  # Closure itself grants no connection or identity result.


@pytest.mark.parametrize(
    "error,kind",
    [(TimeoutError, "timeout"), (ValueError, "byte_limit"), (OSError, "connection_error")],
)
def test_transport_faults_still_fail_closed(error, kind):
    module = tunnel()
    policy = module.TunnelPolicy()
    policy.transport_error(error("synthetic-secret-canary"))
    assert policy.abort.is_set() and policy.allowed == 0
    assert policy.diagnostics()["transport_events"] == [kind]
    assert "synthetic-secret-canary" not in str(policy.diagnostics())


def test_real_loopback_tunnel_forwards_without_parsing_tls_or_logging(capsys):
    module = tunnel()
    upstream, peer = socket.socketpair()
    policy = module.TunnelPolicy(lambda: upstream)
    service = module.server(policy)
    worker = Thread(target=service.serve_forever)
    worker.start()
    try:
        with socket.create_connection(service.server_address, timeout=3) as client:
            peer.settimeout(3)
            client.sendall(
                b"CONNECT sts.us-east-1.amazonaws.com:443 HTTP/1.1\r\n"
                b"Host: sts.us-east-1.amazonaws.com:443\r\n\r\n"
            )
            received = b""
            while b"\r\n\r\n" not in received:
                received += client.recv(4096)
            assert received.startswith(b"HTTP/1.0 200")
            client.sendall(b"synthetic-opaque-tls-bytes")
            assert peer.recv(1024) == b"synthetic-opaque-tls-bytes"
            peer.sendall(b"synthetic-response")
            assert client.recv(1024) == b"synthetic-response"
        assert policy.summary() == {
            "connection_attempts": 1,
            "allowed_tunnels": 1,
            "blocked_reasons": [],
        }
        assert not capsys.readouterr().out
    finally:
        peer.close()
        policy.abort.set()
        service.shutdown()
        service.server_close()
        worker.join(timeout=5)
        assert not worker.is_alive()
