#!/usr/bin/env python3
"""End-to-end: fixtures -> split -> assemble two recipes -> validate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))


def assert_fixture_taxonomy() -> None:
    catalog = ROOT.parent / "workspace" / "catalog" / "atoms.jsonl"
    rows = [json.loads(ln) for ln in catalog.read_text(encoding="utf-8").splitlines() if ln.strip()]
    by_src = {}
    for a in rows:
        by_src.setdefault(a["source"]["template_id"], []).append(a)
    screen = by_src.get("factory-energy-screen") or []
    roles = {a["role"] for a in screen}
    assert "hero" in roles and "kpi" in roles and "deco-corner" in roles, roles
    maps = [a for a in screen if a["kind"] == "map"]
    assert maps and maps[0]["placement"]["hero_ok"]
    kpis = [a for a in screen if a["kind"] == "kpi"]
    assert kpis and all(not a["placement"]["hero_ok"] for a in kpis)
    dash = by_src.get("sales-dashboard") or []
    assert any(a["kind"] == "query" for a in dash)
    ecom = [a for a in rows if a["source"]["template_id"].startswith("电商")]
    if ecom:
        pic_heroes = [
            a
            for a in ecom
            if a["kind"] == "media" and a["placement"]["hero_ok"] and a["role"] == "hero"
        ]
        assert pic_heroes, "ecommerce C-position picture should be hero_ok"
        assert max(a["size"]["area_ratio"] for a in pic_heroes) >= 0.18
    print("fixture taxonomy OK")


def main() -> None:
    py = sys.executable
    run([py, "generate_fixtures.py"])
    run([py, "split_atoms.py", "--replace"])
    assert_fixture_taxonomy()
    run(
        [
            py,
            "assemble_det2.py",
            "--recipe",
            "screen-hero-center",
            "--name",
            "工厂能耗监控中心",
        ]
    )
    run(
        [
            py,
            "assemble_det2.py",
            "--recipe",
            "dashboard-filter-kpi-main",
            "--name",
            "销售经营看板",
        ]
    )
    run(
        [
            py,
            "assemble_det2.py",
            "--recipe",
            "screen-left-hero",
            "--name",
            "左侧主图监控大屏",
        ]
    )
    run([py, "review_heroes.py"])
    out = ROOT.parent / "workspace" / "out"
    for det2 in sorted(out.glob("*.DET2")):
        run([py, "validate_det2.py", str(det2)])
    catalog = ROOT.parent / "workspace" / "catalog" / "atoms.jsonl"
    n = len([ln for ln in catalog.read_text(encoding="utf-8").splitlines() if ln.strip()])
    summary = {
        "atoms": n,
        "outputs": [p.name for p in sorted(out.glob("*.DET2"))],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
