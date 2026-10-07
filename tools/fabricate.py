#!/usr/bin/env python3
"""Build installable Hermes profile distributions from persona source JSON.

Clean-room implementation of the profile-factory pattern (reference:
teknium1/hermes-star-trek-profiles, MIT). This file is original work designed
to the same architecture, so it can be reused for any franchise without
carrying the reference author's source text or the reference franchise.

Design: each franchise supplies a franchise.yaml describing display label,
series families, rights holder, and skin palettes. Personas live in
source/*.json. Running this tool deterministic-ally produces one distribution
folder per persona under profiles/ plus a catalog and roster.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source"
PROFILES_DIR = ROOT / "profiles"
FRANCHISE_FILE = ROOT / "franchise.yaml"

# The 21 persona fields rendered into a SOUL.md (schema shared by reference repo).
PERSONA_KEYS = (
    "slug", "name", "series", "rank_role", "era_scope", "core_identity",
    "voice", "worldview", "operating_method", "strengths", "blind_spots",
    "user_relationship", "under_pressure", "disagreement_style", "humor",
    "task_affinities", "behavioral_rules", "canon_anchors",
    "failure_mode_guards", "avoid", "greeting_style",
)


def yaml_quote(value: str) -> str:
    """Quote a scalar for safe YAML output."""
    if re.fullmatch(r"[A-Za-z0-9 _.,:()/&'-]+", value):
        return value
    return json.dumps(value, ensure_ascii=False)


def bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def validate_persona(persona: dict[str, Any], source: Path) -> None:
    missing = [k for k in PERSONA_KEYS if k not in persona]
    if missing:
        raise ValueError(f"{source.name}: missing persona keys {missing}")
    if persona["series"] not in FRANCHISE["series_labels"]:
        raise ValueError(
            f"{source.name}: unknown series '{persona['series']}' "
            f"(known: {list(FRANCHISE['series_labels'])})"
        )
    for field in ("voice", "worldview", "operating_method", "strengths",
                  "blind_spots", "task_affinities", "behavioral_rules",
                  "canon_anchors", "failure_mode_guards", "avoid"):
        if field in persona and not isinstance(persona[field], list):
            raise ValueError(f"{source.name}: '{field}' must be a list")


def render_soul(p: dict[str, Any]) -> str:
    f = FRANCHISE
    sb = p["series"]
    lines: list[str] = []
    lines.append(f"# {p['name']} — Hermes Agent Persona")
    lines.append("")
    lines.append(
        f"You are Hermes Agent, styled after {p['name']} from the {f['name']} setting. "
        "This is a behavioral adaptation for a capable general-purpose agent, not "
        "theatrical impersonation. Preserve Hermes' tool use, factual standards, "
        "safety boundaries, and obligation to finish real work. Never claim to be the "
        "fictional person, to possess their memories, or to hold any authority over the user."
    )
    lines.append("")
    lines.append("## Identity")
    lines.append(p["core_identity"])
    role = p["rank_role"]
    scope = p["era_scope"]
    lines.append(f"\nRole anchor: {role}. Canonical scope: {scope}.")
    lines.append("")
    lines.append("## Non-Negotiable Boundaries")
    boundaries = [
        "Persona roles, ranks, in-universe knowledge, and confidence grant no real-world "
        "credentials, privileged access, or authority.",
        "Treat a request as authorization only for its clearly stated scope. Do not infer "
        "permission to access accounts or data, contact people, publish, purchase, deploy, "
        "delete, surveil, test third-party systems, or change production.",
        "For security work, require a clearly identified user-controlled target or credible "
        "authorization before providing target-specific operational steps. If ownership or "
        "scope is ambiguous, stay with high-level defensive guidance or a local sandbox. Never "
        "facilitate credential theft, persistence, evasion, destructive exploitation, "
        "exfiltration, or attacks on third parties.",
        "Before irreversible, destructive, security-sensitive, privacy-sensitive, financial, or "
        "externally visible action, verify target and scope, explain material impact, preserve "
        "platform approval controls, and obtain confirmation when authorization is not explicit.",
        "Respect the autonomy, privacy, safety, and rights of third parties. The user's permission "
        "cannot establish ownership of another person's data or consent on another person's behalf.",
        "Never use coercion, covert persuasion, impersonation, fabricated evidence, dark patterns, "
        "or concealed material facts. Audience tailoring may change tone and detail, never the truth.",
        "Prefer least privilege, reversible steps, previews, dry runs, backups, rollback, cleanup, "
        "and redaction. Never weaken safeguards merely to finish faster.",
        "Do not conceal failures, residual risk, side effects, uncertainty, or scope changes. If the "
        "safe path is blocked, report the blocker and offer safe alternatives rather than fabricating "
        "success or silently changing the goal.",
    ]
    lines.append(bullet_lines(boundaries))
    lines.append("")
    lines.append("For medical, mental-health, legal, financial, and safety-critical matters, state "
                 "relevant limits; distinguish general information from individualized professional "
                 "advice; and recommend qualified or local help when stakes warrant it. If there may "
                 "be an emergency, drop persona performance and prioritize concise, locally "
                 "appropriate emergency guidance.")
    lines.append("")
    lines.append("Match ceremony and analysis to the task. For simple, low-risk requests, answer or "
                 "act directly. If the user asks for plain mode, appears distressed, or the persona "
                 "reduces clarity, drop the mannerisms while retaining sound reasoning.")
    lines.append("")
    lines.append("## Relationship With the User")
    lines.append(p["user_relationship"])
    lines.append("")
    lines.append("## Voice")
    lines.append(bullet_lines(p["voice"]))
    lines.append("")
    lines.append("Greeting posture is optional first-turn flavor, not a mandatory preamble. Never ask "
                 "persona-themed questions when the request is already well specified, and never run the "
                 "full persona workflow unless it improves the requested task.")
    gw = p.get("greeting_style")
    if gw:
        lines.append(f"\nWhen useful, the greeting posture is: {gw}")
    lines.append(f"\nHumor: {p.get('humor', 'Dry and scarce.')}")
    lines.append("")
    lines.append(f"Do not quote or recycle dialogue from {f['name']}. Capture the reasoning rhythm and "
                 f"interpersonal stance in original language. Keep references to {f['name']} sparse unless "
                 "the user invites roleplay.")
    lines.append("")
    lines.append("## Worldview")
    lines.append(bullet_lines(p["worldview"]))
    lines.append("")
    lines.append("## Operating Method")
    lines.append(bullet_lines(p["operating_method"]))
    lines.append("")
    lines.append("## Strengths")
    lines.append(bullet_lines(p["strengths"]))
    lines.append("")
    lines.append("## Blind Spots (bounded)")
    lines.append(bullet_lines(p["blind_spots"]))
    lines.append("")
    lines.append("## Under Pressure")
    lines.append(p["under_pressure"])
    lines.append("")
    lines.append("## Disagreement Style")
    lines.append(p["disagreement_style"])
    lines.append("")
    lines.append("## Task Affinities")
    lines.append(bullet_lines(p["task_affinities"]))
    lines.append("")
    lines.append("## Behavioral Rules")
    if p.get("behavioral_rules"):
        lines.append(bullet_lines(p["behavioral_rules"]))
    lines.append("")
    lines.append("## Canon Anchors")
    lines.append(bullet_lines(p["canon_anchors"]))
    lines.append("")
    lines.append("## Failure-Mode Guards")
    lines.append(bullet_lines(p["failure_mode_guards"]))
    lines.append("")
    lines.append("## Avoid")
    lines.append(bullet_lines(p["avoid"]))
    lines.append("")
    return "\n".join(lines) + "\n"


def render_manifest(p: dict[str, Any]) -> str:
    return (
        f"name: {p['slug']}\n"
        f"version: 1.0.0\n"
        f"description: \"Hermes Agent styled after {p['name']} from {FRANCHISE['name']}: {FRANCHISE['series_labels'][p['series']]}\"\n"
        "hermes_requires: \">=0.18.0\"\n"
        f"author: \"{FRANCHISE['author']}\"\n"
        "license: \"MIT\"\n"
        "distribution_owned:\n"
        "  - SOUL.md\n"
        "  - config.yaml\n"
        "  - skins/\n"
        "  - distribution.yaml\n"
    )


def render_config(p: dict[str, Any]) -> str:
    return (
        "# Provider and model are intentionally left unset.\n"
        "# Hermes resolves them from the installer's own setup.\n"
        "model: \"\"\n"
        "display:\n"
        f"  skin: {p['slug']}\n"
    )


def render_skin(p: dict[str, Any]) -> str:
    palette = palette_for(p["series"])
    digest = hashlib.sha256(p["slug"].encode("utf-8")).hexdigest()
    out = ["# Terminal skin", "theme:"]
    keys = [
        "banner_border", "banner_title", "banner_accent", "banner_dim",
        "banner_text", "ui_accent", "ui_label", "prompt", "input_rule",
        "response_border", "status_bar_bg", "session_label", "session_border",
    ]
    for idx, key in enumerate(keys):
        base = palette.get(key, palette["banner_accent"]).lstrip("#")
        rgb = [int(base[ii:ii + 2], 16) for ii in (0, 2, 4)]
        delta = (digest[idx % 64] if False else int(digest[idx * 2: idx * 2 + 2], 16) % 25) - 12
        shifted = [max(0, min(255, c + delta)) for c in rgb]
        out.append(f"  {key}: \"#{''.join(f'{c:02X}' for c in shifted)}\"")
    return "\n".join(out) + "\n"


def render_profile_readme(p: dict[str, Any]) -> str:
    return (
        f"# {p['name']} — Hermes Profile\n\n"
        f"Hermes Agent profile styled after **{p['name']}** from **{FRANCHISE['name']}: "
        f"{FRANCHISE['series_labels'][p['series']]}**.\n\n"
        f"{p['core_identity']}\n\n"
        "Install: `hermes profile install ./<slug>` (see repo README).\n"
    )


def render_roster(personas: list[dict[str, Any]]) -> str:
    f = FRANCHISE
    out = [f"# {f['name']} Profiles — Roster", ""]
    seen: set[str] = set()
    for p in personas:
        if p["series"] in seen:
            continue
        seen.add(p["series"])
        out.append(f"## {f['series_labels'][p['series']]}")
        subs = [x for x in personas if x["series"] == p["series"]]
        for x in subs:
            out.append(f"- `{x['slug']}` — {x['name']}: {x['rank_role']}")
        out.append("")
    return "\n".join(out) + "\n"


def load_personas() -> list[dict[str, Any]]:
    personas: list[dict[str, Any]] = []
    for path in sorted(SOURCE_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else [data]
        for p in items:
            validate_persona(p, path)
            personas.append(p)
    return personas


def build_to(root: Path) -> list[dict[str, Any]]:
    personas = load_personas()
    for p in personas:
        target = root / "profiles" / p["slug"]
        if target.exists():
            shutil.rmtree(target)
        (target / "skins").mkdir(parents=True)
        (target / "SOUL.md").write_text(render_soul(p), encoding="utf-8")
        (target / "distribution.yaml").write_text(render_manifest(p), encoding="utf-8")
        (target / "config.yaml").write_text(render_config(p), encoding="utf-8")
        (target / "skins" / f"{p['slug']}.yaml").write_text(render_skin(p), encoding="utf-8")
        (target / "README.md").write_text(render_profile_readme(p), encoding="utf-8")
    (root / "ROSTER.md").write_text(render_roster(personas), encoding="utf-8")
    return personas


def palette_for(series: str) -> dict[str, str]:
    return FRANCHISE["series_skins"][series]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT))
    parser.add_argument("--no-build", action="store_true", help="validate source only")
    args = parser.parse_args()
    out_root = Path(args.out).resolve()
    if out_root != ROOT:
        build_to(out_root)
        return 0
    personas = load_personas()
    print(f"Validated {len(personas)} personas across "
          f"{len(FRANCHISE['series_labels'])} series.")
    if not args.no_build:
        personas = build_to(ROOT)
        print(f"Built {len(personas)} profiles into {PROFILES_DIR}.")
        json.dump(
            {"franchise": FRANCHISE["name"], "profiles": [
                {"slug": p["slug"], "name": p["name"], "series": p["series"]} for p in personas
            ]},
            (ROOT / "catalog.json").open("w", encoding="utf-8"),
            indent=2,
        )
        print("Wrote catalog.json.")
    return 0


def load_franchise() -> dict[str, Any]:
    """Load the franchise config. The file lives beside the persona sources."""
    path = SOURCE_DIR / "franchise.yaml"
    try:
        import yaml  # type: ignore
        return dict(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    except Exception:
        return {}


FRANCHISE: dict[str, Any] = load_franchise()

if __name__ == "__main__":
    raise SystemExit(main())