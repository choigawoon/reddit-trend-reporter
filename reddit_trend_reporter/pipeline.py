"""Optional static-site build step. Only meaningful when run from a checkout
that contains the Vite frontend (package.json); the installed CLI produces
JSON data and leaves rendering/deploy to the repo + GitHub Pages."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def run_build(base_dir: Path) -> None:
    if not (base_dir / "package.json").exists():
        print(f"skip build: no package.json in {base_dir} (data-only run)")
        return
    npm = shutil.which("npm")
    if not npm:
        print("skip build: npm not found on PATH")
        return
    print("+ npm run build")
    subprocess.check_call([npm, "run", "build"], cwd=base_dir)
