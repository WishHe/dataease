#!/usr/bin/env python3
"""Split DET2 templates into atoms + kits."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    CATALOG_DIR,
    FIXTURES_DIR,
    RAW_DIR,
    ensure_dirs,
    load_catalog,
    load_det2,
    slug,
    split_det2,
    write_catalog,
)


def collect_inputs(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    if not paths:
        for folder in (FIXTURES_DIR, RAW_DIR):
            if folder.exists():
                files.extend(sorted(folder.glob("*.DET2")))
        return files
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob("*.DET2")))
        else:
            files.append(path)
    return [f for f in files if f.suffix.upper() == ".DET2"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="*", help="DET2 files or directories")
    parser.add_argument("--replace", action="store_true", help="rebuild catalog from scratch")
    args = parser.parse_args()
    ensure_dirs()

    existing_atoms, existing_kits = ([], []) if args.replace else load_catalog()
    atoms_by_id = {a["id"]: a for a in existing_atoms}
    kits_by_id = {k["id"]: k for k in existing_kits}

    files = collect_inputs(args.inputs)
    if not files:
        raise SystemExit("no DET2 inputs; run generate_fixtures.py or ingest_market.py first")

    full_atoms = {}
    if not args.replace:
        from common import ATOMS_DIR, load_atom

        for aid in atoms_by_id:
            atom_file = ATOMS_DIR / f"{aid}.json"
            if atom_file.exists():
                full_atoms[aid] = load_atom(aid)

    for file in files:
        det = load_det2(file)
        template_id = slug(file.stem)
        new_atoms, kit = split_det2(det, template_id=template_id)
        for atom in new_atoms:
            full_atoms[atom["id"]] = atom
            atoms_by_id[atom["id"]] = atom
        kits_by_id[kit["id"]] = kit
        print(f"split {file.name}: {len(new_atoms)} atoms, kit={kit['id']}")

    write_catalog(list(full_atoms.values()), list(kits_by_id.values()))
    print(f"catalog -> {CATALOG_DIR} ({len(full_atoms)} atoms, {len(kits_by_id)} kits)")


if __name__ == "__main__":
    main()
