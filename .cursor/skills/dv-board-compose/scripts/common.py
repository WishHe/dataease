"""DET2 split / assemble / validate — stdlib only."""

from __future__ import annotations

import copy
import json
import re
import uuid
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
RECIPES_DIR = SKILL_ROOT / "recipes"
WORKSPACE = SKILL_ROOT / "workspace"
ATOMS_DIR = WORKSPACE / "atoms"
CATALOG_DIR = WORKSPACE / "catalog"
FIXTURES_DIR = WORKSPACE / "fixtures"
OUT_DIR = WORKSPACE / "out"
RAW_DIR = WORKSPACE / "raw"

PIXEL_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

KPI_TYPES = {"indicator", "indicator-hold", "gauge", "liquid"}
MAP_TYPES = {"map", "bubble-map", "flow-map", "symbolic-map"}
TABLE_TYPES = {"table-info", "table-normal", "table-pivot", "table-heatmap"}
HERO_TYPES = MAP_TYPES | {"graph", "sankey", "treemap", "circle-packing"}
DECO_COMPONENTS = {
    "DeDecoration",
    "CanvasBoard",
    "CanvasIcon",
    "DynamicBackground",
}
MEDIA_COMPONENTS = {"Picture", "DeVideo", "DeStreamMedia", "DeFrame"}
SHAPE_COMPONENTS = {"RectShape", "CircleShape", "SvgTriangle"}
TITLE_COMPONENTS = {"ScrollText"}

REGIONS_3x3 = [
    ["top-left", "top", "top-right"],
    ["left", "center", "right"],
    ["bottom-left", "bottom", "bottom-right"],
]


def ensure_dirs() -> None:
    for p in (WORKSPACE, ATOMS_DIR, CATALOG_DIR, FIXTURES_DIR, OUT_DIR, RAW_DIR):
        p.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_maybe_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def new_id() -> str:
    return str(uuid.uuid4().int)[:19]


def slug(text: str) -> str:
    text = (text or "unnamed").strip().lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text)
    return text.strip("-")[:48] or "unnamed"


def load_det2(path: Path) -> dict:
    raw = load_json(path)
    return {
        "name": raw.get("name") or path.stem,
        "dvType": raw.get("dvType") or raw.get("dv_type") or "dashboard",
        "nodeType": raw.get("nodeType") or "template",
        "version": raw.get("version") or 3,
        "templateType": raw.get("templateType") or "self",
        "snapshot": raw.get("snapshot") or PIXEL_PNG,
        "canvasStyleData": parse_maybe_json(raw.get("canvasStyleData") or {}),
        "componentData": parse_maybe_json(raw.get("componentData") or []),
        "dynamicData": parse_maybe_json(raw.get("dynamicData") or {}),
        "staticResource": parse_maybe_json(raw.get("staticResource") or {}),
        "appData": raw.get("appData"),
        "_raw": raw,
    }


def dump_det2(path: Path, det: dict) -> None:
    out = {
        "name": det["name"],
        "dvType": det["dvType"],
        "nodeType": det.get("nodeType", "template"),
        "version": int(det.get("version") or 3),
        "templateType": det.get("templateType", "self"),
        "snapshot": det.get("snapshot") or PIXEL_PNG,
        "canvasStyleData": stringify(det["canvasStyleData"]),
        "componentData": stringify(det["componentData"]),
        "dynamicData": stringify(det["dynamicData"]),
        "staticResource": stringify(det.get("staticResource") or {}),
        "appData": det.get("appData"),
    }
    dump_json(path, out)


def canvas_size(style: dict, dv_type: str) -> tuple[float, float]:
    w = float(style.get("width") or (1920 if dv_type == "dataV" else 1600))
    h = float(style.get("height") or (1080 if dv_type == "dataV" else 900))
    return w, h


def component_geom(
    comp: dict,
    dv_type: str,
    canvas_w: float,
    canvas_h: float,
    offset: tuple[float, float] = (0.0, 0.0),
    tab_box: dict | None = None,
    tab_extent: tuple[float, float] | None = None,
) -> dict:
    """Pixel box on the root canvas.

    Group / dataV-tab children store left/top relative to the parent; pass the
    parent's absolute origin as `offset`. Dashboard tab children use an inner
    72-column grid mapped into `tab_box` (the DeTabs cell).
    """
    style = comp.get("style") or {}
    if dv_type == "dashboard":
        x = float(comp.get("x") or 1)
        y = float(comp.get("y") or 1)
        sx = float(comp.get("sizeX") or 18)
        sy = float(comp.get("sizeY") or 8)
        if tab_box is not None:
            mx, my = tab_extent or (72.0, 36.0)
            mx, my = max(mx, 1.0), max(my, 1.0)
            left = tab_box["left"] + (x - 1) / mx * tab_box["width"]
            top = tab_box["top"] + (y - 1) / my * tab_box["height"]
            width = sx / mx * tab_box["width"]
            height = sy / my * tab_box["height"]
        else:
            mx, my = 72.0, 36.0
            left = (x - 1) / mx * canvas_w
            top = (y - 1) / my * canvas_h
            width = sx / mx * canvas_w
            height = sy / my * canvas_h
        return {
            "left": left,
            "top": top,
            "width": width,
            "height": height,
            "x": x,
            "y": y,
            "sizeX": sx,
            "sizeY": sy,
        }
    left = offset[0] + float(style.get("left") or 0)
    top = offset[1] + float(style.get("top") or 0)
    width = float(style.get("width") or 200)
    height = float(style.get("height") or 120)
    return {
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "x": 0,
        "y": 0,
        "sizeX": 0,
        "sizeY": 0,
    }


def apply_geom(comp: dict, dv_type: str, geom: dict, canvas_w: float, canvas_h: float) -> None:
    style = comp.setdefault("style", {})
    if dv_type == "dashboard":
        x = int(geom.get("x") or 1)
        y = int(geom.get("y") or 1)
        sx = int(geom.get("sizeX") or 18)
        sy = int(geom.get("sizeY") or 8)
        comp["x"], comp["y"], comp["sizeX"], comp["sizeY"] = x, y, sx, sy
        style["left"] = (x - 1) / 72.0 * canvas_w
        style["top"] = (y - 1) / 36.0 * canvas_h
        style["width"] = sx / 72.0 * canvas_w
        style["height"] = sy / 36.0 * canvas_h
        return
    style["left"] = float(geom["left"])
    style["top"] = float(geom["top"])
    style["width"] = float(geom["width"])
    style["height"] = float(geom["height"])


def region_of(cx: float, cy: float, canvas_w: float, canvas_h: float) -> str:
    col = 0 if cx < canvas_w / 3 else (2 if cx > canvas_w * 2 / 3 else 1)
    row = 0 if cy < canvas_h / 3 else (2 if cy > canvas_h * 2 / 3 else 1)
    return REGIONS_3x3[row][col]


def guess_theme(style: dict, dv_type: str) -> str:
    bg = str(style.get("backgroundColor") or "").lower()
    dash = (style.get("dashboard") or {}).get("themeColor")
    if dv_type == "dashboard" and dash == "light":
        return "light"
    if any(k in bg for k in ("00e5", "00c8", "0aa", "cyan")):
        return "dark-cyan"
    if any(k in bg for k in ("0a2a", "0b1", "1a3", "003")):
        return "dark-blue"
    if bg.startswith("#0") or bg.startswith("#1") or "rgb(2" in bg:
        return "dark"
    if dv_type == "dataV":
        return "dark"
    return "light"


def collect_palette(comp: dict, view: dict | None) -> list[str]:
    colors = []
    bg = (comp.get("commonBackground") or {}).get("backgroundColor")
    if isinstance(bg, str) and bg.startswith("#"):
        colors.append(bg)
    if view:
        basic = ((view.get("customAttr") or {}).get("basicStyle") or {})
        for c in basic.get("colors") or []:
            if isinstance(c, str):
                colors.append(c)
    return colors[:6]


def collect_resource_keys(obj: Any) -> set[str]:
    keys: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str) and "static-resource" in node:
            keys.add(node)

    walk(obj)
    return keys


def flatten_components(components: list, parent: str | None = None) -> list[tuple[dict, str | None]]:
    out: list[tuple[dict, str | None]] = []
    for node in walk_tree(components, parent=parent):
        out.append((node["comp"], node["parent"]))
    return out


def _tab_extent(children: list) -> tuple[float, float]:
    if not children:
        return 72.0, 36.0
    max_x = 72.0
    max_y = 36.0
    for ch in children:
        x = float(ch.get("x") or 1)
        y = float(ch.get("y") or 1)
        sx = float(ch.get("sizeX") or 1)
        sy = float(ch.get("sizeY") or 1)
        max_x = max(max_x, x + sx - 1)
        max_y = max(max_y, y + sy - 1)
    return max_x, max_y


def walk_tree(
    components: list,
    *,
    parent: str | None = None,
    offset: tuple[float, float] = (0.0, 0.0),
    tab_box: dict | None = None,
    tab_extent: tuple[float, float] | None = None,
    tab_index: int | None = None,
    container_area: float = 0.0,
    container_origin: str | None = None,
    dv_type: str = "dataV",
    canvas_w: float = 1920.0,
    canvas_h: float = 1080.0,
) -> list[dict]:
    """Flatten Group / DeTabs, carrying absolute origin for nested geom."""
    out: list[dict] = []
    for comp in components or []:
        ctype = comp.get("component")
        if ctype == "GroupArea":
            continue
        out.append(
            {
                "comp": comp,
                "parent": parent,
                "offset": offset,
                "tab_box": tab_box,
                "tab_extent": tab_extent,
                "tab_index": tab_index,
                "container_area": container_area,
                "container_origin": container_origin,
            }
        )
        geom = component_geom(
            comp,
            dv_type,
            canvas_w,
            canvas_h,
            offset=offset,
            tab_box=tab_box,
            tab_extent=tab_extent,
        )
        area = (geom["width"] * geom["height"]) / max(canvas_w * canvas_h, 1)
        origin = region_of(
            geom["left"] + geom["width"] / 2,
            geom["top"] + geom["height"] / 2,
            canvas_w,
            canvas_h,
        )
        if ctype == "DeTabs":
            nested_offset = (geom["left"], geom["top"]) if dv_type == "dataV" else offset
            nested_box = geom if dv_type == "dashboard" else None
            for i, tab in enumerate(comp.get("propValue") or []):
                children = tab.get("componentData") or []
                extent = _tab_extent(children) if dv_type == "dashboard" else None
                out.extend(
                    walk_tree(
                        children,
                        parent=str(comp.get("id") or ""),
                        offset=nested_offset,
                        tab_box=nested_box,
                        tab_extent=extent,
                        tab_index=i,
                        container_area=area,
                        container_origin=origin,
                        dv_type=dv_type,
                        canvas_w=canvas_w,
                        canvas_h=canvas_h,
                    )
                )
        elif ctype == "Group":
            out.extend(
                walk_tree(
                    comp.get("propValue") or [],
                    parent=str(comp.get("id") or ""),
                    offset=(geom["left"], geom["top"]),
                    tab_box=tab_box,
                    tab_extent=tab_extent,
                    tab_index=tab_index,
                    container_area=area,
                    container_origin=origin,
                    dv_type=dv_type,
                    canvas_w=canvas_w,
                    canvas_h=canvas_h,
                )
            )
    return out


def classify(
    comp: dict,
    view: dict | None,
    geom: dict,
    canvas_w: float,
    canvas_h: float,
    container_area: float = 0.0,
) -> dict:
    ctype = comp.get("component")
    chart_type = (view or {}).get("type") or comp.get("innerType") or ""
    area = geom["width"] * geom["height"]
    area_ratio = min(area / max(canvas_w * canvas_h, 1), 1.0)
    cx = geom["left"] + geom["width"] / 2
    cy = geom["top"] + geom["height"] / 2
    origin = region_of(cx, cy, canvas_w, canvas_h)
    near_corner = (
        min(cx, canvas_w - cx) < canvas_w * 0.12 and min(cy, canvas_h - cy) < canvas_h * 0.12
    )
    wide_top = geom["width"] > canvas_w * 0.5 and cy < canvas_h * 0.14
    wide_bottom = geom["width"] > canvas_w * 0.5 and cy > canvas_h * 0.86

    kind = "chart"
    role = "support"
    hero_ok = False

    if ctype == "VQuery":
        kind, role = "query", "filter"
    elif ctype == "DeTimeClock":
        kind, role = "clock", "header"
    elif ctype in TITLE_COMPONENTS or wide_top and ctype in {"UserView"} and chart_type == "rich-text":
        kind, role = "title", "header"
    elif ctype in SHAPE_COMPONENTS:
        kind, role = "shape", "deco-border" if geom["height"] < 40 or geom["width"] < 40 else "kit-skin"
    elif ctype in MEDIA_COMPONENTS:
        full_bleed = area_ratio >= 0.80 or (
            geom["left"] <= canvas_w * 0.03
            and geom["top"] <= canvas_h * 0.03
            and geom["width"] >= canvas_w * 0.92
            and geom["height"] >= canvas_h * 0.92
        )
        aspect = geom["width"] / max(geom["height"], 1)
        thin_bar = geom["height"] < canvas_h * 0.16 and geom["width"] > canvas_w * 0.45
        tall_strip = geom["width"] < canvas_w * 0.22 and geom["height"] > canvas_h * 0.45
        scene_aspect = 0.55 <= aspect <= 2.8
        # Grouped globe / 3D cluster: child may be <12% but the group is the C-position.
        effective = area_ratio
        if container_area >= 0.12 and scene_aspect and area_ratio >= 0.05:
            effective = max(area_ratio, container_area)
        if full_bleed:
            kind, role = "bg", "bg"
        elif near_corner and area_ratio < 0.08:
            kind, role = "media", "deco-corner"
        elif thin_bar or tall_strip or area_ratio < 0.08:
            kind, role = "media", "kit-skin"
        elif effective >= 0.12 and scene_aspect:
            kind, role, hero_ok = "media", "support", True
        else:
            kind, role = "media", "support"
    elif ctype in DECO_COMPONENTS:
        if area_ratio >= 0.4:
            kind, role = "bg", "bg"
        elif near_corner:
            kind, role = "deco", "deco-corner"
        else:
            kind, role = "deco", "deco-border"
    elif ctype == "UserView":
        if chart_type in KPI_TYPES:
            kind, role = "kpi", "kpi"
        elif chart_type in TABLE_TYPES:
            kind, role = "table", "support"
            hero_ok = area_ratio >= 0.16
        elif chart_type in MAP_TYPES:
            kind, role, hero_ok = "map", "support", True
        elif chart_type in HERO_TYPES:
            kind, role, hero_ok = "chart", "support", True
        else:
            kind, role = "chart", "support"
            hero_ok = area_ratio >= 0.16
        if wide_bottom and kind == "chart":
            role = "footer"
        if wide_top and kind in {"title", "chart"}:
            role = "header"
    else:
        kind, role = "shape", "kit-skin"

    if kind == "kpi":
        hero_ok = False
        prefer = [origin, "top-left", "top", "top-right"]
        avoid = ["center"]
    elif role == "hero":
        prefer = ["center", origin]
        avoid = ["top-left", "top-right"]
    elif role == "filter":
        prefer = ["top-row", "top"]
        avoid = ["center"]
    elif role == "header":
        prefer = ["top", "top-row"]
        avoid = ["center", "bottom"]
    elif role == "footer":
        prefer = ["bottom", "bottom-row"]
        avoid = ["center"]
    elif role.startswith("deco"):
        prefer = [origin]
        avoid = ["center"]
        hero_ok = False
    elif role == "bg":
        prefer = ["full"]
        avoid = []
        hero_ok = False
    else:
        prefer = [origin, "right", "left"]
        avoid = []

    density = "high" if area_ratio < 0.08 else ("low" if area_ratio > 0.22 else "medium")
    return {
        "kind": kind,
        "chart_type": chart_type or kind,
        "role": role,
        "placement": {
            "origin_region": origin,
            "prefer": list(dict.fromkeys(prefer)),
            "avoid": avoid,
            "hero_ok": bool(hero_ok),
        },
        "density": density,
        "area_ratio": round(area_ratio, 4),
    }


def index_without_payload(atom: dict) -> dict:
    slim = copy.deepcopy(atom)
    slim.pop("payload", None)
    return slim


def _effective_hero_area(atom: dict) -> float:
    area = (atom.get("size") or {}).get("area_ratio") or 0
    tab = (atom.get("source") or {}).get("tab_index")
    cont = (atom.get("size") or {}).get("container_area") or 0
    if tab not in (None, 0):
        return area * 0.12
    if tab == 0 and cont:
        return max(area, cont) + area * 0.25
    return area


def _hero_center_bonus(atom: dict) -> float:
    if _effective_hero_area(atom) < 0.12:
        return 0.0
    origin = (atom.get("placement") or {}).get("origin_region") or ""
    if origin == "center":
        return 0.18
    if origin == "top":
        return 0.04
    return 0.0


def pick_canonical_hero(atoms: list[dict]) -> dict | None:
    """One C-position per kit, matching market cover layout.

    Maps beat pictures unless a much larger scene picture is the 3D underlay.
    Non-first tab children are demoted. Center origin beats a slightly larger
    bottom chart (dashboard tab vs footer).
    """
    def usable(a: dict) -> bool:
        if a.get("chart_type") == "rich-text":
            return False
        if a.get("kind") not in {"map", "media", "chart", "table"}:
            return False
        return a.get("role") not in {"bg", "kpi", "filter", "header", "deco-corner", "deco-border"}

    content = [a for a in atoms if usable(a)]
    maps = [a for a in content if a["kind"] == "map"]
    pics = [
        a
        for a in content
        if a["kind"] == "media" and a.get("placement", {}).get("hero_ok")
    ]
    charts = [a for a in content if a["kind"] == "chart"]
    tables = [a for a in content if a["kind"] == "table"]

    def best(pool: list[dict]) -> dict | None:
        if not pool:
            return None
        return max(pool, key=lambda a: _effective_hero_area(a) + _hero_center_bonus(a))

    best_map, best_pic = best(maps), best(pics)
    if best_pic and best_map:
        if _effective_hero_area(best_pic) >= 1.5 * max(_effective_hero_area(best_map), 0.01):
            return best_pic
        return best_map
    if best_map:
        return best_map
    if best_pic:
        return best_pic
    ranked = []
    for a in charts + tables:
        kind_w = 0.08 if a["kind"] == "chart" else 0.0
        ranked.append((_effective_hero_area(a) + _hero_center_bonus(a) + kind_w, a))
    ranked = [x for x in ranked if x[0] > 0.05]
    if not ranked:
        return None
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[0][1]


def assign_canonical_hero(atoms: list[dict]) -> dict | None:
    for atom in atoms:
        if atom.get("role") == "hero":
            atom["role"] = "support"
    winner = pick_canonical_hero(atoms)
    if not winner:
        return None
    winner["role"] = "hero"
    winner.setdefault("placement", {})["hero_ok"] = True
    prefer = winner["placement"].setdefault("prefer", [])
    winner["placement"]["prefer"] = list(dict.fromkeys(["center"] + prefer))
    winner["placement"]["avoid"] = ["top-left", "top-right"]
    return winner


def canvas_bg_picture(url: str, canvas_w: float, canvas_h: float) -> dict:
    cid = new_id()
    left, top = canvas_w * 0.20, canvas_h * 0.14
    width, height = canvas_w * 0.60, canvas_h * 0.58
    return {
        "id": cid,
        "component": "Picture",
        "name": "图片",
        "label": "图片",
        "innerType": "Picture",
        "isShow": True,
        "x": 1,
        "y": 1,
        "sizeX": 36,
        "sizeY": 14,
        "propValue": {"url": url, "flip": {"horizontal": False, "vertical": False}},
        "style": {
            "rotate": 0,
            "opacity": 1,
            "adaptation": "adaptation",
            "left": left,
            "top": top,
            "width": width,
            "height": height,
        },
        "commonBackground": {
            "backgroundColorSelect": False,
            "backgroundImageEnable": False,
            "innerPadding": 0,
            "borderRadius": 0,
        },
    }


def maybe_canvas_scene_hero(det: dict, atoms: list[dict], canvas_w: float, canvas_h: float) -> dict | None:
    """C-position is often the canvas background photo (community / aerial), not a Picture."""
    if det.get("dvType") != "dataV":
        return None
    if any(a.get("kind") == "map" for a in atoms):
        return None
    if any(a.get("kind") == "media" and a.get("placement", {}).get("hero_ok") for a in atoms):
        return None
    if any(
        a.get("kind") in {"chart", "table"}
        and a.get("chart_type") != "rich-text"
        and (a.get("size", {}).get("area_ratio") or 0) >= 0.12
        for a in atoms
    ):
        return None
    style = det.get("canvasStyleData") or {}
    bg = style.get("background")
    if not isinstance(bg, str) or "static-resource" not in bg:
        return None
    return canvas_bg_picture(bg, canvas_w, canvas_h)


def split_det2(det: dict, template_id: str | None = None) -> tuple[list[dict], dict]:
    dv_type = det["dvType"]
    style = det["canvasStyleData"] if isinstance(det["canvasStyleData"], dict) else {}
    canvas_w, canvas_h = canvas_size(style, dv_type)
    theme = guess_theme(style, dv_type)
    template_id = template_id or slug(det.get("name") or "template")
    kit_id = f"kit-{template_id}"
    views = det.get("dynamicData") or {}
    if isinstance(views, str):
        views = json.loads(views)
    # dynamicData keys may be number-like strings
    view_map = {str(k): v for k, v in views.items()}

    atoms: list[dict] = []
    for node in walk_tree(
        det.get("componentData") or [],
        dv_type=dv_type,
        canvas_w=canvas_w,
        canvas_h=canvas_h,
    ):
        comp = node["comp"]
        parent = node["parent"]
        cid = str(comp.get("id") or new_id())
        view = view_map.get(cid)
        geom = component_geom(
            comp,
            dv_type,
            canvas_w,
            canvas_h,
            offset=node["offset"],
            tab_box=node["tab_box"],
            tab_extent=node["tab_extent"],
        )
        meta = classify(
            comp, view, geom, canvas_w, canvas_h, container_area=node["container_area"] or 0
        )
        resource_keys = sorted(collect_resource_keys(comp) | collect_resource_keys(view or {}))
        notes = []
        if parent:
            notes.append(f"parent={parent}")
        if node["tab_index"] is not None:
            notes.append(f"tab={node['tab_index']}")
        atom = {
            "id": f"{template_id}__{cid}",
            "source": {
                "template_id": template_id,
                "template_name": det.get("name"),
                "origin_component_id": cid,
                "tab_index": node["tab_index"],
            },
            "dv_type": dv_type,
            "kind": meta["kind"],
            "chart_type": meta["chart_type"],
            "role": meta["role"],
            "placement": meta["placement"],
            "size": {
                "w": round(geom["width"], 2),
                "h": round(geom["height"], 2),
                "sizeX": geom["sizeX"],
                "sizeY": geom["sizeY"],
                "aspect": round(geom["width"] / max(geom["height"], 1), 3),
                "area_ratio": meta["area_ratio"],
                "container_area": round(node["container_area"] or 0, 4),
                "resizable": [0.75, 1.25],
            },
            "theme": theme,
            "industry": [],
            "scene": [],
            "visual": {
                "density": meta["density"],
                "has_3d": bool((comp.get("multiDimensional") or {}).get("enable")),
                "palette": collect_palette(comp, view),
            },
            "compat": {
                "kit": kit_id,
                "slot_min": {
                    "w": round(geom["width"] * 0.6, 1),
                    "h": round(geom["height"] * 0.6, 1),
                },
            },
            "payload": {
                "component": copy.deepcopy(comp),
                "view": copy.deepcopy(view) if view else None,
                "resource_keys": resource_keys,
            },
            "notes": " ".join(notes),
        }
        atoms.append(atom)

    scene = maybe_canvas_scene_hero(det, atoms, canvas_w, canvas_h)
    if scene:
        geom = component_geom(scene, dv_type, canvas_w, canvas_h)
        meta = classify(scene, None, geom, canvas_w, canvas_h)
        bg_url = (scene.get("propValue") or {}).get("url")
        atoms.append(
            {
                "id": f"{template_id}__{scene['id']}",
                "source": {
                    "template_id": template_id,
                    "template_name": det.get("name"),
                    "origin_component_id": str(scene["id"]),
                    "tab_index": None,
                    "from_canvas_bg": True,
                },
                "dv_type": dv_type,
                "kind": "media",
                "chart_type": "Picture",
                "role": "support",
                "placement": {
                    **meta["placement"],
                    "hero_ok": True,
                    "prefer": ["center"],
                    "avoid": ["top-left", "top-right"],
                },
                "size": {
                    "w": round(geom["width"], 2),
                    "h": round(geom["height"], 2),
                    "sizeX": 0,
                    "sizeY": 0,
                    "aspect": round(geom["width"] / max(geom["height"], 1), 3),
                    "area_ratio": meta["area_ratio"],
                    "container_area": 0,
                    "resizable": [0.75, 1.25],
                },
                "theme": theme,
                "industry": [],
                "scene": [],
                "visual": {"density": meta["density"], "has_3d": False, "palette": []},
                "compat": {
                    "kit": kit_id,
                    "slot_min": {"w": round(geom["width"] * 0.6, 1), "h": round(geom["height"] * 0.6, 1)},
                },
                "payload": {
                    "component": scene,
                    "view": None,
                    "resource_keys": [bg_url] if bg_url else [],
                },
                "notes": "from_canvas_bg",
            }
        )

    assign_canonical_hero(atoms)

    kit = {
        "id": kit_id,
        "dv_type": dv_type,
        "theme": theme,
        "source_template": template_id,
        "canvas_style": copy.deepcopy(style),
        "static_resource": copy.deepcopy(det.get("staticResource") or {}),
        "snapshot": det.get("snapshot") or PIXEL_PNG,
        "bg_atom_ids": [a["id"] for a in atoms if a["role"] == "bg"],
        "deco_atom_ids": [a["id"] for a in atoms if a["role"].startswith("deco")],
        "atom_ids": [a["id"] for a in atoms],
    }
    return atoms, kit


def write_catalog(atoms: list[dict], kits: list[dict]) -> None:
    ensure_dirs()
    for atom in atoms:
        dump_json(ATOMS_DIR / f"{atom['id']}.json", atom)
    with (CATALOG_DIR / "atoms.jsonl").open("w", encoding="utf-8") as f:
        for atom in atoms:
            f.write(json.dumps(index_without_payload(atom), ensure_ascii=False) + "\n")
    dump_json(CATALOG_DIR / "kits.json", kits)


def load_catalog() -> tuple[list[dict], list[dict]]:
    atoms: list[dict] = []
    jsonl = CATALOG_DIR / "atoms.jsonl"
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            if line.strip():
                atoms.append(json.loads(line))
    kits = load_json(CATALOG_DIR / "kits.json") if (CATALOG_DIR / "kits.json").exists() else []
    return atoms, kits


def load_atom(atom_id: str) -> dict:
    return load_json(ATOMS_DIR / f"{atom_id}.json")


def load_recipe(recipe_id: str) -> dict:
    path = RECIPES_DIR / f"{recipe_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"recipe not found: {recipe_id}")
    return load_json(path)


def score_atom(atom: dict, slot: dict, preferred_kit: str | None, used: set[str]) -> float:
    if atom["id"] in used:
        return -1e9
    if atom["dv_type"] != slot.get("_dv_type"):
        return -1e9
    if preferred_kit and atom.get("compat", {}).get("kit") != preferred_kit:
        return -1e9
    req = slot.get("require") or {}
    if req.get("hero_ok") and not atom.get("placement", {}).get("hero_ok"):
        return -1e9
    if atom["role"] in {"bg", "deco-corner", "deco-border", "kit-skin"}:
        return -1e9
    if slot.get("role") == "hero" and atom["kind"] in {"deco", "query", "clock", "kpi"}:
        return -1e9
    if slot.get("role") != "hero" and atom.get("role") == "hero":
        return -1e9
    if slot.get("role") == "kpi" and atom["kind"] == "media":
        return -1e9
    if slot.get("role") == "hero" and atom["kind"] == "media" and not atom.get("placement", {}).get(
        "hero_ok"
    ):
        return -1e9
    score = 0.0
    if atom["role"] == slot["role"]:
        score += 50
    elif slot["role"] == "hero" and atom["placement"].get("hero_ok"):
        score += 35
    elif slot["role"] == "support" and atom["kind"] in {"chart", "table", "map", "media"}:
        score += 20
    elif slot["role"] == "footer" and atom["kind"] == "chart":
        score += 25
    elif slot["role"] == "header" and atom["kind"] in {"title", "clock"}:
        score += 40
    else:
        score -= 8
    area = (atom.get("size") or {}).get("area_ratio") or 0
    if slot.get("role") == "hero":
        score += min(area, 0.6) * 40
    region = slot.get("region")
    prefer = atom.get("placement", {}).get("prefer") or []
    avoid = atom.get("placement", {}).get("avoid") or []
    if region in prefer:
        score += 15
    if region in avoid:
        score -= 40
    if preferred_kit and atom.get("compat", {}).get("kit") == preferred_kit:
        score += 25
    elif preferred_kit:
        score -= 40
    return score


def pick_kit(index: list[dict], kits: list[dict], recipe: dict) -> dict:
    dv_type = recipe["dv_type"]
    needed = [s["role"] for s in recipe["slots"] if not s.get("optional")]
    best, best_score = None, -1
    for kit in kits:
        if kit["dv_type"] != dv_type:
            continue
        members = [a for a in index if a.get("compat", {}).get("kit") == kit["id"]]
        roles = {a["role"] for a in members}
        score = sum(10 for r in needed if r in roles)
        score += 8 if kit.get("deco_atom_ids") else 0
        if any(a.get("role") == "hero" or a.get("placement", {}).get("hero_ok") for a in members):
            score += 15
        # atom count is only a weak tie-breaker, otherwise the largest template always wins
        score += 1 if len(kit.get("atom_ids") or []) >= 40 else 0
        if score > best_score:
            best, best_score = kit, score
    if not best:
        raise RuntimeError(f"no kit for dv_type={dv_type}")
    return best


def pick_atoms(index: list[dict], recipe: dict, kit: dict) -> dict[str, str]:
    used: set[str] = set()
    mapping: dict[str, str] = {}
    for slot in recipe["slots"]:
        slot = dict(slot)
        slot["_dv_type"] = recipe["dv_type"]
        ranked = sorted(
            index,
            key=lambda a: score_atom(a, slot, kit["id"], used),
            reverse=True,
        )
        chosen = None
        for atom in ranked:
            if score_atom(atom, slot, kit["id"], used) < 0:
                continue
            chosen = atom
            break
        if not chosen:
            if slot.get("optional"):
                continue
            # same-kit content fallback, then any
            pool = [
                a
                for a in index
                if a["id"] not in used
                and a["dv_type"] == recipe["dv_type"]
                and a["role"] not in {"bg", "deco-corner", "deco-border", "kit-skin"}
                and (slot["role"] == "hero" or a.get("role") != "hero")
            ]
            same_kit = [a for a in pool if a.get("compat", {}).get("kit") == kit["id"]]
            candidates = same_kit or pool
            if slot["role"] == "hero":
                charts = [
                    a
                    for a in candidates
                    if a["kind"] in {"chart", "map", "table"}
                    or (a["kind"] == "media" and a.get("placement", {}).get("hero_ok"))
                ]
                candidates = charts or candidates
                candidates = sorted(
                    candidates,
                    key=lambda a: (
                        bool(a.get("placement", {}).get("hero_ok")),
                        a["kind"] == "media",
                        a.get("size", {}).get("area_ratio") or 0,
                    ),
                    reverse=True,
                )
            chosen = candidates[0] if candidates else None
        if not chosen:
            raise RuntimeError(f"no atom for slot {slot['id']} role={slot['role']}")
        used.add(chosen["id"])
        mapping[slot["id"]] = chosen["id"]
    return mapping


def remap_ids(comp: dict, view: dict | None, id_map: dict[str, str]) -> tuple[dict, dict | None]:
    old = str(comp.get("id"))
    new = id_map.get(old) or new_id()
    id_map[old] = new
    comp = copy.deepcopy(comp)
    comp["id"] = new
    new_view = None
    if view:
        new_view = copy.deepcopy(view)
        new_view["id"] = new
        new_view["sceneId"] = 0
        new_view["dataFrom"] = "template"
    return comp, new_view


def relative_geom(atom: dict, kit: dict) -> dict:
    cw, ch = canvas_size(kit.get("canvas_style") or {}, atom["dv_type"])
    geom = component_geom(atom["payload"]["component"], atom["dv_type"], cw, ch)
    return {
        "nx": geom["left"] / max(cw, 1),
        "ny": geom["top"] / max(ch, 1),
        "nw": geom["width"] / max(cw, 1),
        "nh": geom["height"] / max(ch, 1),
        "sizeX": geom["sizeX"],
        "sizeY": geom["sizeY"],
        "x": geom["x"],
        "y": geom["y"],
    }


def assemble(recipe: dict, kit: dict, slot_atoms: dict[str, str], name: str) -> dict:
    dv_type = recipe["dv_type"]
    canvas = recipe.get("canvas") or {}
    canvas_w = float(canvas.get("width") or 1920)
    canvas_h = float(canvas.get("height") or 1080)
    style = copy.deepcopy(kit.get("canvas_style") or {})
    style["width"] = canvas_w
    style["height"] = canvas_h
    components: list[dict] = []
    views: dict[str, dict] = {}
    resources: dict[str, Any] = copy.deepcopy(kit.get("static_resource") or {})
    id_map: dict[str, str] = {}

    def add_atom(atom: dict, geom: dict | None, keep_relative: bool = False) -> None:
        comp = copy.deepcopy(atom["payload"]["component"])
        view = copy.deepcopy(atom["payload"]["view"]) if atom["payload"].get("view") else None
        comp, view = remap_ids(comp, view, id_map)
        if keep_relative:
            rel = relative_geom(atom, kit)
            if dv_type == "dashboard":
                apply_geom(
                    comp,
                    dv_type,
                    {
                        "x": atom["payload"]["component"].get("x") or 1,
                        "y": atom["payload"]["component"].get("y") or 1,
                        "sizeX": atom["size"].get("sizeX") or 18,
                        "sizeY": atom["size"].get("sizeY") or 8,
                    },
                    canvas_w,
                    canvas_h,
                )
            else:
                apply_geom(
                    comp,
                    dv_type,
                    {
                        "left": rel["nx"] * canvas_w,
                        "top": rel["ny"] * canvas_h,
                        "width": rel["nw"] * canvas_w,
                        "height": rel["nh"] * canvas_h,
                    },
                    canvas_w,
                    canvas_h,
                )
        elif geom:
            apply_geom(comp, dv_type, geom, canvas_w, canvas_h)
        components.append(comp)
        if view:
            views[str(comp["id"])] = view
        for key in atom["payload"].get("resource_keys") or []:
            if key in (kit.get("static_resource") or {}):
                resources[key] = kit["static_resource"][key]

    if recipe.get("copy_kit_skin"):
        for atom_id in (kit.get("bg_atom_ids") or []) + (kit.get("deco_atom_ids") or []):
            add_atom(load_atom(atom_id), None, keep_relative=True)

    slot_by_id = {s["id"]: s for s in recipe["slots"]}
    for slot_id, atom_id in slot_atoms.items():
        add_atom(load_atom(atom_id), slot_by_id[slot_id]["geom"], keep_relative=False)

    return {
        "name": name,
        "dvType": dv_type,
        "nodeType": "template",
        "version": 3,
        "templateType": "self",
        "snapshot": kit.get("snapshot") or PIXEL_PNG,
        "canvasStyleData": style,
        "componentData": components,
        "dynamicData": views,
        "staticResource": resources,
        "appData": None,
    }


def overlap_ratio(a: dict, b: dict) -> float:
    ax1, ay1, ax2, ay2 = a["left"], a["top"], a["left"] + a["width"], a["top"] + a["height"]
    bx1, by1, bx2, by2 = b["left"], b["top"], b["left"] + b["width"], b["top"] + b["height"]
    ix = max(0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0, min(ay2, by2) - max(ay1, by1))
    inter = ix * iy
    if inter <= 0:
        return 0.0
    area = min(a["width"] * a["height"], b["width"] * b["height"])
    return inter / max(area, 1)


def validate_det2(det: dict) -> list[str]:
    errors: list[str] = []
    dv_type = det.get("dvType")
    if dv_type not in {"dataV", "dashboard"}:
        errors.append(f"invalid dvType: {dv_type}")
    style = det.get("canvasStyleData")
    comps = det.get("componentData")
    views = det.get("dynamicData")
    if not isinstance(style, dict):
        errors.append("canvasStyleData must be object after parse")
        return errors
    if not isinstance(comps, list) or not comps:
        errors.append("componentData empty")
        return errors
    if not isinstance(views, dict):
        errors.append("dynamicData must be object")
        views = {}
    canvas_w, canvas_h = canvas_size(style, dv_type or "dataV")
    if not det.get("snapshot"):
        errors.append("missing snapshot")
    if int(det.get("version") or 0) < 2:
        errors.append("version should be 3")

    geoms = []
    view_ids = {str(k) for k in views.keys()}
    for comp in comps:
        cid = str(comp.get("id") or "")
        if not cid:
            errors.append("component missing id")
            continue
        if comp.get("component") == "UserView" and cid not in view_ids:
            errors.append(f"UserView {cid} missing dynamicData")
        geom = component_geom(comp, dv_type, canvas_w, canvas_h)
        if geom["width"] <= 1 or geom["height"] <= 1:
            errors.append(f"{cid} invalid size")
        if dv_type == "dataV":
            if geom["left"] + geom["width"] < -20 or geom["top"] + geom["height"] < -20:
                errors.append(f"{cid} outside canvas")
            if geom["left"] > canvas_w + 20 or geom["top"] > canvas_h + 20:
                errors.append(f"{cid} outside canvas")
        if comp.get("component") == "UserView":
            geoms.append((cid, geom, comp))

    for i in range(len(geoms)):
        for j in range(i + 1, len(geoms)):
            ratio = overlap_ratio(geoms[i][1], geoms[j][1])
            if ratio > 0.45:
                errors.append(f"views overlap {geoms[i][0]} vs {geoms[j][0]} ({ratio:.2f})")

    has_view = any(c.get("component") == "UserView" for c in comps)
    if not has_view:
        errors.append("no UserView")
    return errors
