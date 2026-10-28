"""Deterministic command/filesystem simulation; not EC2 or systemd execution."""

import hashlib
import importlib.util
import json
import subprocess
from contextlib import nullcontext
from fnmatch import fnmatchcase
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
UUID = "11111111-2222-3333-4444-555555555555"


def load_host():
    spec = importlib.util.spec_from_file_location("host_preflight", ROOT / "infra/aws/host/host.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Machine:
    def __init__(self, tmp_path, monkeypatch):
        self.root, self.monkeypatch = tmp_path, monkeypatch
        self.calls, self.signatures, self.mounted = [], [], False
        self.running, self.format_fault, self.mount_source = False, None, None
        self.c = {
            "volume_id": "vol-00000000000000000",
            "expires_at": "2030-01-02T00:00:00Z",
            "app_image": "synthetic/app@sha256:fixture",
            "postgres_image": "synthetic/pg@sha256:fixture",
        }
        for name in ("opt/fata", "dev/disk/by-id", "etc/systemd/system", "srv"):
            (tmp_path / name).mkdir(parents=True, exist_ok=True)
        (tmp_path / "etc/fstab").write_text("")
        self.device = (
            tmp_path / "dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol00000000000000000"
        )
        self.device.touch()
        for name, raw in {
            "host.py": b"synthetic-reviewed-helper",
            "config.json": json.dumps(self.c).encode(),
            "compose.release.yaml": b"synthetic-compose",
        }.items():
            (tmp_path / "opt/fata" / name).write_bytes(raw)
        names = ("host.py", "config.json", "compose.release.yaml")
        (tmp_path / "opt/fata/bundle.json").write_text(
            json.dumps(
                {
                    n: hashlib.sha256((tmp_path / "opt/fata" / n).read_bytes()).hexdigest()
                    for n in names
                }
            )
        )
        self.restart_runtime()

    def path(self, *parts):
        p = Path(*parts)
        if p.is_relative_to(self.root):
            return p
        text = str(p).replace("\\", "/")
        return self.root / text.lstrip("/") if text.startswith("/") else p

    def restart_runtime(self):
        h = self.host = load_host()
        self.monkeypatch.setattr(h, "Path", self.path)
        self.monkeypatch.setattr(h, "BASE", self.root / "opt/fata")
        self.monkeypatch.setattr(h, "DATA", self.root / "srv/fata")
        self.monkeypatch.setattr(h, "run", self.run)
        self.monkeypatch.setattr(h, "host_lock", nullcontext)
        self.monkeypatch.setattr(h, "attest_tools", lambda c: None)
        self.monkeypatch.setattr(h, "window", lambda c: None)
        self.monkeypatch.setattr(h, "guard", lambda: None)
        self.monkeypatch.setattr(h.time, "sleep", lambda delay: pytest.fail("Uncontrolled wait"))

    def run(self, *args, **kwargs):
        self.calls.append(args)
        output, status = b"", 0
        if args[:2] == ("systemctl", "is-active"):
            status = 0 if self.running else 3
        elif args[0] == "lsblk":
            output = b"disk 0\n"
        elif args[0] == "wipefs":
            output = json.dumps({"signatures": self.signatures}).encode()
        elif args[0] == "mkfs.ext4":
            if self.format_fault == "before":
                raise RuntimeError("interrupted_format")
            self.signatures = [{"type": "ext4"}]
            if self.format_fault == "after":
                raise RuntimeError("lost_format_result")
        elif args[0] == "blkid":
            output = (UUID + "\n").encode()
        elif args[0] == "findmnt":
            status = 0 if self.mounted else 1
            output = f"{self.mount_source or self.device} {UUID} ext4\n".encode()
            assert "--mountpoint" in args
        elif args[0] == "mount":
            self.mounted = True
        return subprocess.CompletedProcess(args, status, output, b"")


@pytest.fixture
def machine(tmp_path, monkeypatch):
    return Machine(tmp_path, monkeypatch)


@pytest.mark.parametrize("as_string", [False, True])
def test_simulated_paths_already_in_sandbox_are_unchanged(machine, as_string):
    for path in (machine.root, machine.device, machine.root / "not-created/device"):
        assert machine.path(str(path) if as_string else path) == path


@pytest.mark.parametrize("path", ["/dev/disk/by-id/device", "/etc/fstab", "/srv/fata"])
def test_host_absolute_paths_are_mapped_once_into_sandbox(machine, path):
    expected = machine.root / path.lstrip("/")
    assert machine.path(path) == expected
    assert machine.path(expected) == machine.path(str(expected)) == expected


def test_simulated_path_mapping_uses_components_not_string_prefix(machine):
    machine.root = Path("/simulated")
    assert machine.path("/simulated-other/device") == machine.root / "simulated-other/device"
    assert machine.path("relative/device") == Path("relative/device")
    assert machine.path(machine.root, "dev", "device") == machine.root / "dev/device"


def test_delayed_attachment_uses_controlled_barrier(machine):
    machine.device.unlink()
    waits = []

    def attach(delay):
        waits.append(delay)
        if len(waits) == 2:
            machine.device.touch()

    assert machine.host.wait_device(machine.c, attempts=3, pause=attach) == machine.device
    assert waits == [2, 2] and not machine.calls


def test_attachment_timeout_then_explicit_retry_after_restart(machine):
    machine.device.unlink()
    waits = []
    with pytest.raises(RuntimeError, match="data_volume_missing"):
        machine.host.wait_device(machine.c, attempts=3, pause=waits.append)
    assert len(waits) == 3 and not machine.calls
    machine.device.touch()
    machine.restart_runtime()
    machine.host.prepare(machine.c)
    assert (machine.host.BASE / "storage.json").exists()


@pytest.mark.parametrize("signatures", [[{"type": "ext4"}], [{"type": "gpt"}]])
def test_existing_signature_never_formatted(machine, signatures):
    machine.signatures = signatures
    if signatures[0]["type"] == "ext4":
        machine.host.prepare(machine.c)
    else:
        with pytest.raises(RuntimeError):
            machine.host.prepare(machine.c)
    assert not any(c[0] == "mkfs.ext4" for c in machine.calls)


@pytest.mark.parametrize("point", ["before", "after"])
def test_interrupted_format_never_blindly_repeats(machine, point):
    machine.format_fault = point
    with pytest.raises(RuntimeError):
        machine.host.prepare(machine.c)
    assert (machine.host.BASE / "format-intent.json").exists()
    machine.format_fault = None
    machine.restart_runtime()
    if point == "before":
        with pytest.raises(RuntimeError, match="uncertain_volume_initialization"):
            machine.host.prepare(machine.c)
    else:
        machine.host.prepare(machine.c)
    assert sum(c[0] == "mkfs.ext4" for c in machine.calls) == 1


@pytest.mark.parametrize("point", ["daemon.json", "storage.json", "fata.conf"])
def test_preparation_interrupted_atomic_write_then_restarts_safely(machine, monkeypatch, point):
    original = machine.host.atomic_text

    def fail(path, text):
        if path.name == point:
            raise RuntimeError("simulated_process_exit")
        original(path, text)

    monkeypatch.setattr(machine.host, "atomic_text", fail)
    with pytest.raises(RuntimeError):
        machine.host.prepare(machine.c)
    assert not any(c[:2] == ("systemctl", "unmask") for c in machine.calls)
    machine.restart_runtime()
    machine.host.prepare(machine.c)
    machine.host.mount_check(machine.c)
    assert sum(c[0] == "mkfs.ext4" for c in machine.calls) == 1


def test_repeated_prepare_with_existing_mount_is_idempotent(machine):
    machine.host.prepare(machine.c)
    first = (machine.root / "etc/fstab").read_bytes()
    machine.restart_runtime()
    machine.host.prepare(machine.c)
    assert first == (machine.root / "etc/fstab").read_bytes()
    assert sum(c[0] == "mkfs.ext4" for c in machine.calls) == 1
    assert sum(c[0] == "mount" for c in machine.calls) == 1
    assert not any(c[0] == "docker" for c in machine.calls)
    assert not any(c[:2] == ("systemctl", "start") and "docker.service" in c for c in machine.calls)


@pytest.mark.parametrize("missing", ["bundle.json", "host.py", "config.json"])
def test_incomplete_cloud_init_fails_closed(machine, missing):
    (machine.host.BASE / missing).unlink()
    with pytest.raises((RuntimeError, FileNotFoundError)):
        machine.host.prepare(machine.c)
    assert machine.calls[0] == ("systemctl", "mask", "docker.service", "docker.socket")
    assert not any(c[0] == "mkfs.ext4" or c[:2] == ("systemctl", "unmask") for c in machine.calls)


@pytest.mark.parametrize("fault", ["unmounted", "wrong_source", "changed_uuid", "wrong_volume"])
def test_launch_never_uses_root_directory_or_wrong_mount(machine, fault):
    machine.host.prepare(machine.c)
    if fault == "unmounted":
        machine.mounted = False
    elif fault == "wrong_source":
        machine.mount_source = machine.root / "root-disk"
    else:
        p = machine.host.BASE / "storage.json"
        record = json.loads(p.read_text())
        record["uuid" if fault == "changed_uuid" else "volume_id"] = "incorrect"
        p.write_text(json.dumps(record))
    machine.calls.clear()
    with pytest.raises(RuntimeError):
        machine.host.start(machine.c)
    assert not any(c[0] in ("docker", "aws") for c in machine.calls)


@pytest.mark.parametrize(
    "entry",
    ["UUID=incorrect /srv/fata ext4 defaults 0 2\n", f"UUID={UUID} /srv/fata xfs defaults 0 2\n"],
)
def test_invalid_mount_configuration_still_fails_before_mount_or_launch(machine, entry):
    machine.signatures = [{"type": "ext4"}]
    (machine.root / "etc/fstab").write_text(entry)
    with pytest.raises(RuntimeError, match="mount_configuration_conflict"):
        machine.host.prepare(machine.c)
    assert not any(c[0] in ("mount", "mkfs.ext4", "docker", "aws") for c in machine.calls)
    assert not any(c[:2] == ("systemctl", "unmask") for c in machine.calls)


def test_active_docker_requires_explicit_stop_before_prepare(machine):
    machine.running = True
    with pytest.raises(RuntimeError, match="preparation_requires_stopped_docker"):
        machine.host.prepare(machine.c)
    assert not any(c[0] in ("wipefs", "mkfs.ext4") for c in machine.calls)


def test_daemon_pre_start_rechecks_identity_not_only_mount_existence(machine):
    machine.host.prepare(machine.c)
    unit = (machine.root / "etc/systemd/system/docker.service.d/fata.conf").read_text()
    assert "ExecStartPre=/usr/bin/python3 /opt/fata/host.py mount-check" in unit
    assert "Requires=fata-guard.service fata-prepare.service" in unit
    assert "prepare-host" in (machine.root / "etc/systemd/system/fata-prepare.service").read_text()
    image = json.loads((machine.host.BASE / "images.json").read_text())["services"]["postgres"]
    assert image["user"] == "999:999" and image["cap_drop"] == ["ALL"]


def test_prefix_recommendation_is_not_equivalent_to_exact_owner():
    caller = "AROAEXAMPLE000000000001:operator-a"
    other = caller + "-other"
    assert fnmatchcase(other, caller + "*")
    assert caller != other
    # No undocumented tag suffix is silently treated as same-owner evidence.


@pytest.mark.parametrize(
    "options,location,accepted",
    [
        (["name=seccomp,profile=builtin"], "/srv/fata/docker", True),
        (["name=userns"], "/srv/fata/docker", False),
        (["name=rootless"], "/srv/fata/docker", False),
        ([], "/var/lib/docker", False),
    ],
)
def test_daemon_identity_mapping_and_data_root_are_checked(
    options, location, accepted, monkeypatch
):
    h = load_host()
    monkeypatch.setattr(
        h,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(
            a, 0, json.dumps({"SecurityOptions": options, "DockerRootDir": location}).encode(), b""
        ),
    )
    if accepted:
        h.verify_daemon()
    else:
        with pytest.raises(RuntimeError):
            h.verify_daemon()


def test_bootstrap_masks_before_writes_and_records_complete_bundle():
    text = (ROOT / "infra/aws/deployment/bootstrap.sh.tftpl").read_text()
    assert text.index("systemctl mask --now") < text.index("install -d")
    assert text.index("write(folder / 'bundle.json'") > text.index("for name, encoded")
    assert "systemctl enable fata-prepare.service" in text
    assert "systemctl start fata-prepare.service" in text


@pytest.mark.parametrize(
    "option,accepted", [("no-new-privileges:true", True), ("no-new-privileges:false", False)]
)
def test_pg_verification_does_not_accept_disabled_privilege_guard(monkeypatch, option, accepted):
    h = load_host()
    monkeypatch.setattr(h, "mount_check", lambda c: None)
    monkeypatch.setattr(h, "config", lambda: {})
    monkeypatch.setattr(h, "guard", lambda: None)
    monkeypatch.setattr(
        h.urllib.request, "urlopen", lambda *a, **k: nullcontext(SimpleNamespace(status=200))
    )
    app = {
        "Config": {"User": "10001:10001"},
        "HostConfig": {
            "ReadonlyRootfs": True,
            "NetworkMode": "host",
            "Privileged": False,
            "CapDrop": ["ALL"],
            "Binds": [],
        },
    }
    pg = {
        "Config": {"User": "999:999"},
        "HostConfig": {
            "NetworkMode": "host",
            "CapDrop": ["ALL"],
            "Privileged": False,
            "SecurityOpt": [option],
        },
    }

    def run(*args, **kwargs):
        if args[0] == "docker":
            output = json.dumps([pg if args[-1].endswith("postgres-1") else app]).encode()
        else:
            output = b"LISTEN 0 1 127.0.0.1:8000 0.0.0.0:*\nLISTEN 0 1 127.0.0.1:55432 0.0.0.0:*\n"
        return subprocess.CompletedProcess(args, 0, output, b"")

    monkeypatch.setattr(h, "run", run)
    if accepted:
        h.verify()
    else:
        with pytest.raises(RuntimeError, match="unsafe_database_container_configuration"):
            h.verify()
