# SPDX-FileCopyrightText: 2026 Contributors to the RISCV UnifiedDB <https://github.com/riscv/riscv-unified-db>
# SPDX-License-Identifier: BSD-3-Clause-Clear

"""Build the sdist and wheel, then smoke-test the wheel in an isolated environment."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .common import ROOT, DevError, entrypoint

OUTPUT = ROOT / "gen/package-test"


def smoke_command(uv: str, wheel: Path) -> list[str]:
    return [
        uv,
        "run",
        "--isolated",
        "--no-project",
        "--python",
        sys.executable,
        "--with",
        str(wheel),
        "python",
        "-I",
        "installed_smoke.py",
        "--root",
        "output",
        "--full-config",
        "full-config.yaml",
    ]


def smoke_environment() -> dict[str, str]:
    """Hide the checkout environment and every tool on PATH from the installed wheel."""
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("PYTHON", "VIRTUAL_ENV", "UV_PROJECT"))
    }
    environment["PATH"] = ""
    return environment


def main() -> int:
    uv = shutil.which("uv")
    if uv is None:
        raise DevError("uv is required for package acceptance", 2)
    shutil.rmtree(OUTPUT, ignore_errors=True)
    dist = OUTPUT / "dist"
    # uv builds the sdist first, then builds the wheel from that sdist.
    status = subprocess.run([uv, "build", "--out-dir", str(dist), str(ROOT)], check=False)
    if status.returncode:
        return status.returncode
    wheel = next(dist.glob("*.whl"))
    work = OUTPUT / "smoke"
    work.mkdir()
    shutil.copy2(ROOT / "tests/package/installed_smoke.py", work)
    shutil.copy2(ROOT / "cfgs/mc100-32-full-example.yaml", work / "full-config.yaml")
    return subprocess.run(
        smoke_command(uv, wheel), cwd=work, env=smoke_environment(), check=False
    ).returncode


if __name__ == "__main__":
    raise SystemExit(entrypoint(main))
