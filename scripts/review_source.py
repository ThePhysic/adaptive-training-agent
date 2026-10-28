"""Offline source grammar and byte-identity checks; no imports of application code.

Review ZIPs contain only Git-visible public working-tree files, never ignored
private/dependency state. Manifests bind raw bytes, not Git blobs or normalized text.
"""

import argparse
import ast
import fnmatch
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
FORMAT = "working-tree-review-v1"
MEMBER = "_review/source-manifest.json"
PRIVATE = {
    ".git",
    ".aws",
    ".cache",
    ".tools",
    ".venv",
    ".terraform",
    ".codex",
    ".agents",
    "__pycache__",
    "node_modules",
    "dist",
    "AGENTS.md",
    # Reserved private evaluation paths: filter names before any content read.
    "sealed-cases",
    "private-evaluation",
    "reviewer-materials",
    "blinding-keys",
}
PATTERNS = (
    "*.pyc",
    "*.pyo",
    "*.zip",
    "*.tfstate",
    "*.tfstate.*",
    "*.tfplan",
    "*.tfplan.*",
    "*.tfvars",
    "*.tfvars.json",
    "*.tfbackend",
    "backend.hcl",
    "crash.log",
)


def public(name):
    path = PurePosixPath(name)
    return (
        not path.is_absolute()
        and path.as_posix() == name
        and bool(path.parts)
        and all(
            p.lower() not in {item.lower() for item in PRIVATE} and p not in {".", ".."}
            for p in path.parts
        )
        and not any(p.lower().startswith(".env") and p != ".env.example" for p in path.parts)
        and not any(fnmatch.fnmatchcase(path.name.lower(), p) for p in PATTERNS)
        and ":" not in name
        and "\\" not in name
    )


def owned(root, name):
    if not public(name):
        raise ValueError("private_or_noncanonical_review_path")
    path = root / name
    if not path.resolve(strict=True).is_relative_to(root.resolve()):
        raise ValueError("review_path_escape")
    for part in (path, *path.parents):
        if part.is_symlink() or part.is_junction():
            raise ValueError("review_link_rejected")
        if part == root:
            break
    if not path.is_file():
        raise ValueError("review_file_required")
    return path


def inventory(root=ROOT):
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
        timeout=10,
    )
    names = sorted({n for n in result.stdout.decode("utf-8").split("\0") if n and public(n)})
    return {name: owned(root, name) for name in names}


def digest(body):
    return hashlib.sha256(body).hexdigest()


def manifest_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def inspect(root=ROOT):
    files = {}
    python_count = 0
    for name, path in inventory(root).items():
        body = path.read_bytes()
        if name.endswith(".py"):
            ast.parse(body, filename=name)
            ast.parse(body, filename=name, feature_version=(3, 13))
            python_count += 1
        files[name] = digest(body)
    return {
        "format": FORMAT,
        "runtime": sys.version.split()[0],
        "grammar": ["native", "3.13"],
        "python_files": python_count,
        "files": files,
    }


def verify(snapshot, root=ROOT):
    current = inspect(root)
    # Runtime is provenance, not a content hash; another review host can verify
    # the same bytes without pretending to be the original execution host.
    if {k: v for k, v in snapshot.items() if k != "runtime"} != {
        k: v for k, v in current.items() if k != "runtime"
    }:
        raise ValueError("review_snapshot_drift")
    return current


def verify_archive(path, snapshot, root=ROOT):
    verify(snapshot, root)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(snapshot["files"]) | {MEMBER}:
            raise ValueError("review_archive_inventory_mismatch")
        if archive.getinfo(MEMBER).file_size > 2097152:
            raise ValueError("review_archive_manifest_oversized")
        manifest = archive.read(MEMBER)
        if manifest != manifest_bytes(snapshot):
            raise ValueError("review_archive_manifest_mismatch")
        for name, expected in snapshot["files"].items():
            entry = archive.getinfo(name)
            source = owned(root, name).read_bytes()
            if digest(source) != expected:
                raise ValueError("review_source_changed_during_verification")
            if entry.file_size != len(source) or archive.read(name) != source:
                raise ValueError("review_archive_bytes_mismatch")
    verify(snapshot, root)
    return {
        "files": len(snapshot["files"]),
        "python_files": snapshot["python_files"],
        "all_members_byte_identical": True,
        "archive_sha256": digest(path.read_bytes()),
    }


def create_archive(path, snapshot, root=ROOT):
    verify(snapshot, root)
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, expected in snapshot["files"].items():
            body = owned(root, name).read_bytes()
            if digest(body) != expected:
                raise ValueError("review_source_changed_during_packaging")
            archive.writestr(name, body)
        archive.writestr(MEMBER, manifest_bytes(snapshot))
    # Failed/partial ZIPs are retained, never called verified or silently replaced.
    return verify_archive(path, snapshot, root)


def local_artifact(path):
    path = path.absolute()
    if not path.resolve().is_relative_to((ROOT / ".cache").resolve()):
        raise ValueError("review_artifact_must_be_ignored_local_cache")
    for parent in (path, *path.parents):
        if parent.is_symlink() or parent.is_junction():
            raise ValueError("review_artifact_link_rejected")
        if parent == ROOT:
            break
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("check", "snapshot", "verify", "archive", "verify-archive")
    )
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "check":
            value = inspect()
            result = {
                "python_files": value["python_files"],
                "grammar": value["grammar"],
                "pass": True,
            }
        else:
            if args.manifest is None:
                raise ValueError("review_manifest_required")
            path = local_artifact(args.manifest)
            if args.action == "snapshot":
                value = inspect()
                with path.open("xb") as stream:
                    stream.write(manifest_bytes(value))
                result = {
                    "python_files": value["python_files"],
                    "files": len(value["files"]),
                    "pass": True,
                }
            else:
                value = json.loads(path.read_text(encoding="utf-8"))
                if args.action == "verify":
                    verify(value)
                    result = {"snapshot_unchanged": True, "files": len(value["files"])}
                else:
                    if args.archive is None:
                        raise ValueError("review_archive_required")
                    archive = local_artifact(args.archive)
                    result = (create_archive if args.action == "archive" else verify_archive)(
                        archive, value
                    )
        print(json.dumps(result))
    except (
        OSError,
        ValueError,
        SyntaxError,
        subprocess.SubprocessError,
        zipfile.BadZipFile,
        KeyError,
        TypeError,
    ):
        print("review_source_check_failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
