"""Run locked schema/mock checks with Docker --network none; never calls AWS.

Mount /source read-only, /tool Terraform Linux binary, /mirror public provider
mirror read-only and /work an ignored writable local cache. No SDK credentials.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix="f402-", dir="/work") as temporary:
    root = Path(temporary)
    shutil.copytree(
        "/source/infra", root / "infra", ignore=shutil.ignore_patterns(".terraform", "__pycache__")
    )
    (root / "scripts").mkdir()
    shutil.copyfile(
        "/source/scripts/check_infrastructure.py", root / "scripts/check_infrastructure.py"
    )
    shutil.copyfile("/source/compose.release.yaml", root / "compose.release.yaml")
    shutil.copyfile("/tool/terraform", root / "terraform")
    (root / "terraform").chmod(0o700)
    (root / "plugin-cache").mkdir()
    rc = root / "mirror.rc"
    rc.write_text(
        "disable_checkpoint = true\nprovider_installation {\n"
        ' filesystem_mirror {\n path = "/mirror"\n'
        ' include = ["registry.terraform.io/hashicorp/aws"]\n }\n'
        "}\n"
    )
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(root),
        "CHECKPOINT_DISABLE": "1",
        "TF_CLI_CONFIG_FILE": str(rc),
        "TF_PLUGIN_CACHE_DIR": str(root / "plugin-cache"),
        "AWS_EC2_METADATA_DISABLED": "true",
    }
    for module in ("deployment", "state-bootstrap", "modules/protected-bucket"):
        result = subprocess.run(
            [
                str(root / "terraform"),
                "-chdir=infra/aws/" + module,
                "init",
                "-backend=false",
                "-input=false",
                "-lockfile=readonly",
            ],
            cwd=root,
            env=env,
            capture_output=True,
            timeout=180,
        )
        if result.returncode:
            raise SystemExit(result.stderr.decode())
    result = subprocess.run(
        ["python", "scripts/check_infrastructure.py", "--terraform", str(root / "terraform")],
        cwd=root,
        env=env,
        capture_output=True,
        timeout=180,
    )
    if result.returncode:
        raise SystemExit(result.stdout.decode() + result.stderr.decode())
    report = json.loads(result.stdout)
    report["network"] = "Docker --network none"
    report["provider_acquisition"] = "Existing read-only signed-hash mirror, locked checksums"
    print(json.dumps(report, indent=2))
