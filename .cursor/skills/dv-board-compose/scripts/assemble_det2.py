#!/usr/bin/env python3
"""Assemble a new DET2 from recipe + atom catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    OUT_DIR,
    assemble,
    dump_det2,
    ensure_dirs,
    load_catalog,
    load_recipe,
    pick_atoms,
    pick_kit,
    validate_det2,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--name", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--intent", default="", help="optional JSON with titles/name")
    parser.add_argument("--kit", default="", help="force kit id")
    args = parser.parse_args()
    ensure_dirs()

    recipe = load_recipe(args.recipe)
    index, kits = load_catalog()
    if not index:
        raise SystemExit("empty catalog; run split_atoms.py first")
    if args.kit:
        kit = next((k for k in kits if k["id"] == args.kit), None)
        if not kit:
            raise SystemExit(f"kit not found: {args.kit}")
    else:
        kit = pick_kit(index, kits, recipe)
    mapping = pick_atoms(index, recipe, kit)
    intent = {}
    if args.intent:
        intent = json.loads(Path(args.intent).read_text(encoding="utf-8"))
    name = args.name or intent.get("name") or f"AI-{recipe['id']}"
    det = assemble(recipe, kit, mapping, name)
    errors = validate_det2(det)
    out = Path(args.out) if args.out else OUT_DIR / f"{name}-TEMPLATE.DET2"
    dump_det2(out, det)
    print(f"kit={kit['id']}")
    for slot, atom_id in mapping.items():
        print(f"  {slot} <- {atom_id}")
    print(f"wrote {out}")
    if errors:
        print("validate warnings/errors:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
