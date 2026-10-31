#!/usr/bin/env python3
"""Write C-position report: catalog hero vs market-cover verdicts."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import CATALOG_DIR, SKILL_ROOT, load_catalog  # noqa: E402

COVERS = SKILL_ROOT / "reference" / "hero-covers.json"


def main() -> None:
    index, kits = load_catalog()
    if not index:
        raise SystemExit("empty catalog")
    covers = json.loads(COVERS.read_text(encoding="utf-8")) if COVERS.exists() else {}
    by_kit: dict[str, list] = defaultdict(list)
    for atom in index:
        by_kit[atom.get("compat", {}).get("kit") or "unknown"].append(atom)

    lines = [
        "# C 位裁定（市场封面）",
        "",
        "已用 `workspace/screenshots/` 对照每个入库套件封面，由规则选出 **唯一** `role=hero`。",
        "不要把清单交给人勾选。封面与结果不一致时改 `scripts/common.py` 的 `pick_canonical_hero`。",
        "",
        f"kits={len(kits)} atoms={len(index)}",
        "",
        "| 套件 | 封面裁定 | 当前 hero | 结果 |",
        "|------|----------|-----------|------|",
    ]
    mismatches = 0
    for kit in kits:
        src = kit.get("source_template") or ""
        members = by_kit.get(kit["id"], [])
        heroes = [a for a in members if a.get("role") == "hero"]
        spec = covers.get(src) or {}
        expect = spec.get("expect") or {}
        note = spec.get("note") or ""
        if len(heroes) != 1:
            status = f"FAIL 期望 1 个 hero，实际 {len(heroes)}"
            mismatches += 1
            current = ",".join(f"{h.get('kind')}/{h.get('chart_type')}" for h in heroes) or "无"
        else:
            h = heroes[0]
            current = f"{h.get('kind')} {h.get('chart_type')} area={h.get('size', {}).get('area_ratio')}"
            ok = True
            if expect.get("kind") and h.get("kind") != expect["kind"]:
                ok = False
            if expect.get("chart_type") and h.get("chart_type") != expect["chart_type"]:
                ok = False
            status = "OK" if ok else "FAIL"
            if not ok:
                mismatches += 1
        want = expect.get("chart_type") or expect.get("kind") or "?"
        lines.append(f"| `{src}` | {want} — {note} | {current} | **{status}** |")

    lines.append("")
    lines.append("## 各套件 hero 原子")
    lines.append("")
    for kit in kits:
        members = by_kit.get(kit["id"], [])
        heroes = [a for a in members if a.get("role") == "hero"]
        pics = [
            a
            for a in members
            if a.get("kind") in {"media", "bg"} and (a.get("size", {}).get("area_ratio") or 0) >= 0.08
        ]
        lines.append(f"### {kit.get('source_template')} ({kit['dv_type']})")
        lines.append("")
        for a in heroes:
            p = a.get("placement") or {}
            s = a.get("size") or {}
            extra = " canvas-bg" if (a.get("source") or {}).get("from_canvas_bg") or "from_canvas_bg" in (a.get("notes") or "") else ""
            lines.append(
                f"- **hero** `{a['id']}` {a.get('kind')}/{a.get('chart_type')} "
                f"{p.get('origin_region')} area={s.get('area_ratio')}{extra}"
            )
        for a in pics[:4]:
            if a.get("role") == "hero":
                continue
            p = a.get("placement") or {}
            s = a.get("size") or {}
            lines.append(
                f"- pic `{a.get('role')}` {p.get('origin_region')} area={s.get('area_ratio')} "
                f"hero_ok={p.get('hero_ok')}"
            )
        lines.append("")

    out = CATALOG_DIR / "hero-review.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out} mismatches={mismatches}")
    if mismatches:
        raise SystemExit(mismatches)


if __name__ == "__main__":
    main()
