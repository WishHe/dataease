#!/usr/bin/env python3
"""Validate a DET2 file can be imported structurally."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_det2, validate_det2  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()
    det = load_det2(Path(args.file))
    errors = validate_det2(det)
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    views = len(det.get("dynamicData") or {})
    comps = len(det.get("componentData") or [])
    print(f"OK  dvType={det['dvType']} components={comps} views={views} name={det['name']}")


if __name__ == "__main__":
    main()
