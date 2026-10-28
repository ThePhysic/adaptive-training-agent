"""Source grammar and review-archive regressions; no application execution/network."""

import ast
import importlib.util
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def review():
    spec = importlib.util.spec_from_file_location(
        "review_source", ROOT / "scripts/review_source.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_project_owned_python_has_native_and_review_grammar(review):
    result = review.inspect()
    assert result["python_files"] >= 169 and result["grammar"] == ["native", "3.13"]
    assert "AGENTS.md" not in result["files"]
    assert not any(".cache" in Path(p).parts for p in result["files"])


def test_native_314_syntax_explains_old_parser_failure_and_formatter_retains_fix():
    original = "try:\n    pass\nexcept KeyError, TypeError, ValueError:\n    pass\n"
    ast.parse(original)
    with pytest.raises(SyntaxError):
        ast.parse(original, feature_version=(3, 13))
    fixed = (
        "try:\n    pass\nexcept (\n    KeyError,\n    TypeError,\n    ValueError,\n):\n    pass\n"
    )
    tool = ROOT / (".venv/Scripts/ruff.exe" if os.name == "nt" else ".venv/bin/ruff")
    if not tool.is_file():
        tool = shutil.which("ruff")
    result = subprocess.run(
        [str(tool), "format", "--target-version", "py314", "--stdin-filename", "probe.py"],
        input=fixed,
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )
    assert result.stdout == fixed
    assert ast.dump(ast.parse(original)) == ast.dump(
        ast.parse(result.stdout, feature_version=(3, 13))
    )


@pytest.mark.parametrize(
    "name",
    [
        "AGENTS.md",
        ".AWS/config",
        ".cache/private.json",
        ".env",
        "infra/aws/private.tfstate",
        "infra/aws/private.tfvars.json",
        "infra/aws/.terraform/terraform.tfstate",
        "web/node_modules/a.py",
        "../outside.py",
        "C:/outside.py",
        "review.zip",
    ],
)
def test_private_artifacts_and_unsafe_paths_are_excluded(review, name):
    assert not review.public(name)


@pytest.fixture
def sample(review, tmp_path, monkeypatch):
    path = tmp_path / "sample.py"
    path.write_bytes("value = 'synthetic-✓'\r\n".encode())
    monkeypatch.setattr(review, "inventory", lambda root: {"sample.py": path})
    return tmp_path, path, review.inspect(tmp_path)


def test_archive_members_are_raw_byte_identical_including_crlf(review, sample):
    root, source, snapshot = sample
    archive = root / "review.zip"
    result = review.create_archive(archive, snapshot, root)
    assert result["all_members_byte_identical"] and result["python_files"] == 1
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.read("sample.py") == source.read_bytes()
        assert json.loads(zipped.read(review.MEMBER)) == snapshot
    with pytest.raises(FileExistsError):
        review.create_archive(archive, snapshot, root)


def test_changed_source_cannot_be_packaged_as_previously_tested(review, sample):
    root, source, snapshot = sample
    source.write_bytes(source.read_bytes() + b"# post-test change\r\n")
    with pytest.raises(ValueError, match="snapshot_drift"):
        review.create_archive(root / "review.zip", snapshot, root)
    assert not (root / "review.zip").exists()


def test_corrupt_member_cannot_pass_even_with_matching_manifest(review, sample):
    root, _, snapshot = sample
    archive = root / "bad.zip"
    with zipfile.ZipFile(archive, "x") as zipped:
        zipped.writestr("sample.py", "different = True\n")
        zipped.writestr(review.MEMBER, review.manifest_bytes(snapshot))
    with pytest.raises(ValueError, match="bytes_mismatch"):
        review.verify_archive(archive, snapshot, root)


def test_duplicate_archive_member_cannot_pass(review, sample):
    root, source, snapshot = sample
    archive = root / "duplicates.zip"
    with zipfile.ZipFile(archive, "x") as zipped:
        zipped.writestr("sample.py", source.read_bytes())
        with pytest.warns(UserWarning, match="Duplicate"):
            zipped.writestr("sample.py", source.read_bytes())
        zipped.writestr(review.MEMBER, review.manifest_bytes(snapshot))
    with pytest.raises(ValueError, match="inventory_mismatch"):
        review.verify_archive(archive, snapshot, root)


def test_versioned_reference_changes_only_source_provenance():
    directory = ROOT / "data/evaluation/model-v1"
    old = json.loads((directory / "offline-scores-f4-01.json").read_text(encoding="utf-8"))
    new = json.loads((directory / "offline-scores-python-syntax.json").read_text(encoding="utf-8"))
    for key in ("source_files", "source_sha256"):
        assert old["manifest"][key] != new["manifest"][key]
        old["manifest"].pop(key)
        new["manifest"].pop(key)
    assert old == new  # All 150 cases, scores, failures, versions and data fingerprints.
