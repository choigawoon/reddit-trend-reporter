"""Config resolution. The tool no longer assumes it lives inside the repo:
output paths are resolved under a base directory (cwd by default), and the
config file is looked up in a predictable order so the installed CLI can run
anywhere."""
from __future__ import annotations

import json
import os
from importlib import resources
from pathlib import Path
from typing import Any

ENV_CONFIG = "REDDIT_REPORT_CONFIG"
CONFIG_RELPATH = Path("config") / "reddit-report.json"
USER_CONFIG = Path.home() / ".config" / "reddit-trend-reporter" / "reddit-report.json"


def default_config_text() -> str:
    """The packaged starter config, shipped as package data."""
    return (
        resources.files("reddit_trend_reporter")
        .joinpath("data/default-config.json")
        .read_text(encoding="utf-8")
    )


def resolve_config_path(explicit: Path | None, base_dir: Path) -> Path:
    """Find the config file. Order: --config flag, $REDDIT_REPORT_CONFIG,
    <base_dir>/config/reddit-report.json, then the per-user config."""
    if explicit is not None:
        explicit = Path(explicit)
        if not explicit.is_file():
            raise FileNotFoundError(f"config not found: {explicit}")
        return explicit

    candidates: list[Path] = []
    env = os.environ.get(ENV_CONFIG)
    if env:
        candidates.append(Path(env))
    candidates.append(base_dir / CONFIG_RELPATH)
    candidates.append(USER_CONFIG)

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    looked = ", ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"No config found (looked at: {looked}). Run `reddit-report init` to create one."
    )


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
