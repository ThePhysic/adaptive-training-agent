"""Synthetic metadata in a Docker --network none namespace, never host networking."""

import http.client
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def request(address, port):
    connection = http.client.HTTPConnection(address, port, timeout=2)
    try:
        connection.request(
            "PUT", "/latest/api/token", headers={"X-aws-ec2-metadata-token-ttl-seconds": "1"}
        )
        return connection.getresponse().status == 200
    except OSError:
        return False
    finally:
        connection.close()


if sys.argv[1] == "serve":
    for command in [
        ["ip", "link", "set", "lo", "up"],
        ["ip", "addr", "add", "169.254.169.254/32", "dev", "lo"],
        ["ip", "-6", "addr", "add", "fd00:ec2::254/128", "dev", "lo"],
    ]:
        subprocess.run(command, check=True, capture_output=True)

    class Handler(BaseHTTPRequestHandler):
        def do_PUT(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"synthetic-not-an-AWS-token")

        def log_message(self, *args):
            pass

    class IPv6(ThreadingHTTPServer):
        address_family = socket.AF_INET6

    for server in [
        ThreadingHTTPServer(("169.254.169.254", 80), Handler),
        ThreadingHTTPServer(("127.0.0.1", 18080), Handler),
        IPv6(("fd00:ec2::254", 80), Handler),
    ]:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    print("ready", flush=True)
    threading.Event().wait()
elif sys.argv[1] in ("guard", "guard-app-only"):
    spec = importlib.util.spec_from_file_location("host", "/source/infra/aws/host/host.py")
    host = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(host)
    if sys.argv[1] == "guard":
        host.guard()
    else:
        # Reproduce the accepted F4-02 app-only fence inside this isolated namespace.
        for binary, tail in (
            ("iptables", ["!", "-d", "127.0.0.0/8"]),
            ("ip6tables", []),
        ):
            host.run(
                binary,
                "-I",
                "OUTPUT",
                "1",
                "-m",
                "owner",
                "--uid-owner",
                "10001",
                *tail,
                "-j",
                "REJECT",
            )
    print("guarded")
elif sys.argv[1] == "probe":
    uid = int(sys.argv[2])
    os.setgroups([])
    os.setgid(uid)
    os.setuid(uid)
    print(
        json.dumps(
            {
                "uid": uid,
                "ipv4_metadata": request("169.254.169.254", 80),
                "ipv6_metadata": request("fd00:ec2::254", 80),
                "loopback": request("127.0.0.1", 18080),
            }
        )
    )
elif sys.argv[1] == "lock":
    code = """import importlib.util,pathlib,sys,fcntl
s=importlib.util.spec_from_file_location('h','/source/infra/aws/host/host.py')
h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
h.Path=lambda value:pathlib.Path('/tmp/f403a-lock')
if sys.argv[1]=='second':
 with open('/tmp/f403a-lock/prepare.lock','a') as probe:
  try:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:print('blocked',flush=True)
  else:raise AssertionError('Expected owned preparation lock')
with h.host_lock():
 print('entered',flush=True)
 if sys.argv[1]=='first':input()
"""
    children = []
    try:
        first = subprocess.Popen(
            [sys.executable, "-c", code, "first"], stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        children.append(first)
        assert first.stdout.readline() == b"entered\n"
        second = subprocess.Popen([sys.executable, "-c", code, "second"], stdout=subprocess.PIPE)
        children.append(second)
        assert second.stdout.readline() == b"blocked\n"
        first.communicate(b"release\n", timeout=5)
        assert second.communicate(timeout=5)[0] == b"entered\n"
        assert first.returncode == second.returncode == 0
        print("exclusive_lock_waited_then_recovered")
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
