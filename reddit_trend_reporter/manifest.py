"""Profile manifest. `config/profiles.json` is the source registry (which
profiles exist and which config drives each). `sync_manifest` derives the
UI-facing `public/data/profiles.json` from it — so the web app can build a
profile switcher and know where each profile's data lives."""
from __future__ import annotations

import json
from pathlib import Path

from .config import load_config
from .profiles import get_profile

REGISTRY_RELPATH = Path("config") / "profiles.json"
PUBLIC_MANIFEST_RELPATH = Path("public") / "data" / "profiles.json"


def _public_rel(output_path: str) -> str:
    """Map a config output path to the URL the static site serves it at.
    Vite copies `public/` to the site root, so `public/data/x.json` -> `data/x.json`."""
    p = str(output_path).replace("\\", "/")
    if p.startswith("public/"):
        p = p[len("public/") :]
    return p


def sync_manifest(base_dir: Path) -> Path | None:
    registry_path = base_dir / REGISTRY_RELPATH
    if not registry_path.is_file():
        return None
    registry = json.loads(registry_path.read_text())

    out = []
    for entry in registry.get("profiles", []):
        cfg_rel = entry.get("config")
        if not cfg_rel:
            continue
        try:
            cfg = load_config(base_dir / cfg_rel)
        except FileNotFoundError:
            continue
        prof = get_profile(cfg.get("profile"))
        latest_out = cfg.get("output", "public/data/latest.json")
        out.append(
            {
                "id": entry.get("id") or cfg.get("profile", "trend"),
                "label": entry.get("label") or prof["label"],
                "kind": prof["kind"],
                "latest": _public_rel(latest_out),
                "index": _public_rel(cfg.get("public_index", "public/data/index.json")),
                "has_data": (base_dir / latest_out).is_file(),
            }
        )

    manifest_path = base_dir / PUBLIC_MANIFEST_RELPATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"profiles": out}, indent=2, ensure_ascii=False) + "\n")
    return manifest_path
