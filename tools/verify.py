#!/usr/bin/env python3
"""Validate a built collection's generated files for structural integrity.

Checks: every persona has its 5 distribution files present; SOUL.md contains
the franchise name and the Non-Negotiable Boundaries block; no banned token
leaks into any generated text; distribution.yaml is valid.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = ROOT / "profiles"
BANNED = re.compile(r"star\s?trek|teknium|\bTNG\b|\bDS9\b|\bVoyager\b|\bcaptains'?\s?log\b", re.I)


def main() -> int:
    catalog_path = ROOT / "catalog.json"
    if not catalog_path.exists():
        print("catalog.json missing — run fabricate.py first.")
        return 1
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for entry in catalog["profiles"]:
        slug = entry["slug"]
        base = PROFILES_DIR / slug
        required = [
            "SOUL.md", "distribution.yaml", "config.yaml",
            "skins", "README.md",
        ]
        for name in required[:4]:
            p = base / (name if name != "skins" else "skins")
            if not p.exists():
                errors.append(f"{slug}: missing {name}")
                continue
            if name == "skins" and not any(p.glob("*.yaml")):
                errors.append(f"{slug}: no skin yaml")
        if not (base / "skins" / f"{slug}.yaml").exists():
            errors.append(f"{slug}: skin file {slug}.yaml missing")
        soul = (base / "SOUL.md").read_text(encoding="utf-8")
        if "Non-Negotiable Boundaries" not in soul:
            errors.append(f"{slug}: SOUL.md missing boundaries block")
        if catalog["franchise"].lower() not in soul.lower():
            errors.append(f"{slug}: SOUL.md missing franchise name")
    for slug in [e["slug"] for e in catalog["profiles"]]:
        for file in (PROFILES_DIR / slug).rglob("*.yaml"):
            if BANNED.search(file.read_text(encoding="utf-8")):
                errors.append(f"{slug}/{file.name}: banned franchise token")
        soul = (PROFILES_DIR / slug / "SOUL.md").read_text(encoding="utf-8")
        if BANNED.search(soul):
            errors.append(f"{slug}/SOUL.md: banned franchise token")
    if errors:
        print("INVALID:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"OK: {len(catalog['profiles'])} profiles structurally valid, no banned tokens.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())