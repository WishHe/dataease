#!/usr/bin/env python3
"""Build structurally valid DET2 fixtures for the compose pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import PIXEL_PNG, dump_det2, ensure_dirs, FIXTURES_DIR  # noqa: E402


def bg(comp_id: str, **kwargs) -> dict:
    base = {
        "id": comp_id,
        "component": "UserView",
        "canvasId": "canvas-main",
        "category": "base",
        "isShow": True,
        "isLock": False,
        "events": {"checked": False, "type": "jump"},
        "commonBackground": {
            "backgroundColorSelect": True,
            "backgroundColor": "rgba(10, 42, 74, 0.35)",
            "innerImage": "board/board_1.svg",
            "innerPadding": {"mode": "uniform", "top": 8},
        },
        "style": {
            "rotate": 0,
            "opacity": 1,
            "borderActive": False,
            "left": 0,
            "top": 0,
            "width": 200,
            "height": 120,
        },
    }
    base.update(kwargs)
    return base


def view(vid: str, title: str, chart_type: str, extra: dict | None = None) -> dict:
    data = extra or {}
    return {
        "id": vid,
        "title": title,
        "sceneId": 0,
        "tableId": "",
        "type": chart_type,
        "render": "antv",
        "resultCount": 1000,
        "resultMode": "all",
        "chartType": "private",
        "dataFrom": "template",
        "stylePriority": "view",
        "xAxis": data.get("xAxis", [{"id": "f-dim", "name": "类别", "deType": 0, "groupType": "d"}]),
        "yAxis": data.get("yAxis", [{"id": "f-q", "name": "数值", "deType": 2, "groupType": "q", "summary": "sum"}]),
        "xAxisExt": [],
        "yAxisExt": [],
        "customFilter": {},
        "customAttr": {
            "basicStyle": {
                "colorScheme": "default",
                "colors": ["#00E5FF", "#90EE90", "#FAC858"],
                "alpha": 100,
            }
        },
        "customStyle": {"text": {"show": True, "color": "#ffffff", "fontSize": "16"}},
        "senior": {},
        "data": data.get(
            "data",
            {
                "fields": [],
                "tableRow": [{"类别": "A", "数值": 12}, {"类别": "B", "数值": 20}],
            },
        ),
    }


def screen_fixture() -> dict:
    comps = []
    views = {}

    comps.append(
        bg(
            "2000000000000000001",
            component="DynamicBackground",
            innerType="DynamicBackground",
            style={
                "rotate": 0,
                "opacity": 1,
                "left": 0,
                "top": 0,
                "width": 1920,
                "height": 1080,
                "backgroundColor": "rgba(2, 8, 24, 1)",
            },
            commonBackground={"backgroundColorSelect": False},
        )
    )
    for i, pos in enumerate([(8, 8), (1872, 8), (8, 1032), (1872, 1032)]):
        comps.append(
            bg(
                f"200000000000000001{i}",
                component="DeDecoration",
                innerType="DeDecoration",
                name="corner",
                style={
                    "rotate": 0,
                    "opacity": 1,
                    "left": pos[0],
                    "top": pos[1],
                    "width": 40,
                    "height": 40,
                    "color0": "#00E5FF",
                    "color1": "#2862b7",
                },
            )
        )
    comps.append(
        bg(
            "2000000000000000020",
            component="ScrollText",
            innerType="ScrollText",
            name="title",
            propValue="工厂能耗监控中心",
            style={
                "rotate": 0,
                "opacity": 1,
                "left": 80,
                "top": 18,
                "width": 1760,
                "height": 80,
                "fontSize": 32,
                "color": "#00E5FF",
            },
        )
    )

    kpis = [
        ("2000000000000000101", "今日用电", 40, 120),
        ("2000000000000000102", "今日用水", 40, 286),
        ("2000000000000000103", "碳排放", 40, 452),
    ]
    for vid, title, left, top in kpis:
        comps.append(
            bg(
                vid,
                innerType="indicator",
                name=title,
                style={"rotate": 0, "opacity": 1, "left": left, "top": top, "width": 400, "height": 150},
            )
        )
        views[vid] = view(vid, title, "indicator", {"xAxis": [], "yAxis": [{"id": "f-q", "name": title, "deType": 2, "groupType": "q", "summary": "sum"}]})

    comps.append(
        bg(
            "2000000000000000200",
            innerType="map",
            name="厂区能耗分布",
            style={"rotate": 0, "opacity": 1, "left": 460, "top": 120, "width": 1000, "height": 640},
        )
    )
    views["2000000000000000200"] = view("2000000000000000200", "厂区能耗分布", "map")

    comps.append(
        bg(
            "2000000000000000300",
            innerType="bar",
            name="车间用电排名",
            style={"rotate": 0, "opacity": 1, "left": 1480, "top": 120, "width": 400, "height": 400},
        )
    )
    views["2000000000000000300"] = view("2000000000000000300", "车间用电排名", "bar")

    comps.append(
        bg(
            "2000000000000000301",
            innerType="pie",
            name="能耗结构",
            style={"rotate": 0, "opacity": 1, "left": 1480, "top": 540, "width": 400, "height": 220},
        )
    )
    views["2000000000000000301"] = view("2000000000000000301", "能耗结构", "pie")

    comps.append(
        bg(
            "2000000000000000400",
            innerType="line",
            name="近30日用电趋势",
            style={"rotate": 0, "opacity": 1, "left": 40, "top": 780, "width": 1840, "height": 260},
        )
    )
    views["2000000000000000400"] = view("2000000000000000400", "近30日用电趋势", "line")

    return {
        "name": "工厂能耗监控大屏",
        "dvType": "dataV",
        "nodeType": "template",
        "version": 3,
        "templateType": "self",
        "snapshot": PIXEL_PNG,
        "canvasStyleData": {
            "width": 1920,
            "height": 1080,
            "scale": 60,
            "themeId": "10002",
            "color": "#fff",
            "backgroundColor": "#020818",
            "backgroundColorSelect": True,
            "screenAdaptor": "widthFirst",
            "fontFamily": "PingFang",
            "dashboard": {"themeColor": "dark", "gap": "no"},
        },
        "componentData": comps,
        "dynamicData": views,
        "staticResource": {"/static-resource/fixture-bg.png": PIXEL_PNG},
        "appData": None,
    }


def dashboard_fixture() -> dict:
    comps = []
    views = {}

    def cell(vid, inner, title, x, y, sx, sy, chart_type, extra=None):
        comps.append(
            bg(
                vid,
                component="VQuery" if inner == "VQuery" else "UserView",
                innerType=inner,
                name=title,
                x=x,
                y=y,
                sizeX=sx,
                sizeY=sy,
                style={"rotate": 0, "opacity": 1, "width": sx * 22, "height": sy * 22},
                commonBackground={
                    "backgroundColorSelect": True,
                    "backgroundColor": "rgba(255,255,255,0.9)",
                    "innerPadding": {"mode": "uniform", "top": 8},
                },
            )
        )
        if inner != "VQuery":
            views[vid] = view(vid, title, chart_type, extra)

    cell("3000000000000000001", "VQuery", "查询", 1, 1, 72, 4, "query")
    comps[-1]["propValue"] = []
    cell("3000000000000000101", "indicator", "销售额", 1, 5, 18, 6, "indicator", {"xAxis": []})
    cell("3000000000000000102", "indicator", "订单量", 19, 5, 18, 6, "indicator", {"xAxis": []})
    cell("3000000000000000103", "indicator", "客单价", 37, 5, 18, 6, "indicator", {"xAxis": []})
    cell("3000000000000000104", "gauge", "达成率", 55, 5, 18, 6, "gauge", {"xAxis": []})
    cell("3000000000000000200", "bar", "区域销售", 1, 11, 48, 20, "bar")
    cell("3000000000000000300", "line", "月度趋势", 49, 11, 24, 20, "line")

    return {
        "name": "销售经营看板",
        "dvType": "dashboard",
        "nodeType": "template",
        "version": 3,
        "templateType": "self",
        "snapshot": PIXEL_PNG,
        "canvasStyleData": {
            "width": 1600,
            "height": 900,
            "scale": 60,
            "themeId": "10001",
            "color": "#000000",
            "backgroundColor": "#f5f6f7",
            "fontFamily": "PingFang",
            "dashboard": {
                "themeColor": "light",
                "gap": "yes",
                "gapSize": 5,
                "matrixBase": 4,
                "resultMode": "all",
                "resultCount": 1000,
            },
        },
        "componentData": comps,
        "dynamicData": views,
        "staticResource": {},
        "appData": None,
    }


def main() -> None:
    ensure_dirs()
    screen = screen_fixture()
    dash = dashboard_fixture()
    dump_det2(FIXTURES_DIR / "factory-energy-screen.DET2", screen)
    dump_det2(FIXTURES_DIR / "sales-dashboard.DET2", dash)
    print(f"wrote {FIXTURES_DIR / 'factory-energy-screen.DET2'}")
    print(f"wrote {FIXTURES_DIR / 'sales-dashboard.DET2'}")


if __name__ == "__main__":
    main()
