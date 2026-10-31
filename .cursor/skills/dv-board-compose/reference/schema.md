# Schemas

路径均相对技能根目录。JSON 用 UTF-8，脚本不依赖 PyYAML。

## Atom（`atoms/<id>.json`）

三件套必须在同一文件：组件 + 图表配置 + 引用的静态资源 key。

```json
{
  "id": "factory-energy-screen__2000000000000000101",
  "source": {
    "template_id": "factory-energy-screen",
    "template_name": "工厂能耗监控大屏",
    "origin_component_id": "2000000000000000101"
  },
  "dv_type": "dataV",
  "kind": "map",
  "chart_type": "map",
  "role": "hero",
  "placement": {
    "origin_region": "center",
    "prefer": ["center"],
    "avoid": ["top-left", "top-right"],
    "hero_ok": true
  },
  "size": {
    "w": 960,
    "h": 620,
    "sizeX": 0,
    "sizeY": 0,
    "aspect": 1.55,
    "area_ratio": 0.287,
    "resizable": [0.75, 1.25]
  },
  "theme": "dark-cyan",
  "industry": [],
  "scene": [],
  "visual": {
    "density": "medium",
    "has_3d": false,
    "palette": ["#00E5FF", "#0A2A4A"]
  },
  "compat": {
    "kit": "kit-factory-energy-screen",
    "slot_min": { "w": 480, "h": 320 }
  },
  "payload": {
    "component": {},
    "view": {},
    "resource_keys": []
  },
  "notes": ""
}
```

字段约束：

- `id`：`{template_id}__{origin_component_id}`
- `payload.component`：原始组件对象（含 `commonBackground`/`style`）
- `payload.view`：仅 `UserView` 时为 `dynamicData[id]`，否则 `null`
- `payload.resource_keys`：该原子用到的 `staticResource` 键

## Catalog 行（`catalog/atoms.jsonl`）

与 Atom 相同但 **去掉 `payload`**，供检索与提示词。一行一个对象。

## Kit（`catalog/kits.json`）

```json
{
  "id": "kit-factory-energy-screen",
  "dv_type": "dataV",
  "theme": "dark-cyan",
  "source_template": "factory-energy-screen",
  "canvas_style": {},
  "static_resource": {},
  "bg_atom_ids": [],
  "deco_atom_ids": [],
  "atom_ids": []
}
```

组装时：先套 `canvas_style`，再按原子原始相对坐标复制 `bg`/`deco`，最后把内容槽位贴到配方坐标。

## Recipe（`recipes/<id>.json`）

```json
{
  "id": "screen-hero-center",
  "dv_type": "dataV",
  "name": "中央 C 位大屏",
  "canvas": { "width": 1920, "height": 1080, "matrix": { "x": 72, "y": 36 } },
  "kit_required": true,
  "copy_kit_skin": true,
  "slots": [
    {
      "id": "hero",
      "role": "hero",
      "region": "center",
      "require": { "hero_ok": true },
      "geom": { "left": 480, "top": 140, "width": 960, "height": 620 }
    }
  ]
}
```

`geom`：

- 大屏：`left/top/width/height` 像素
- 仪表板：`x/y/sizeX/sizeY` 格；脚本同时回写近似 `style`

可重复槽用相同 `role`、不同 `id`（如 `kpi-1`…`kpi-3`）。

## DET2（导入文件）

与产品导出一致：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 名称 |
| `dvType` | `dataV`/`dashboard` | |
| `nodeType` | `template` | 样式模板 |
| `version` | number | 固定 3 |
| `templateType` | `self` | |
| `snapshot` | dataURL | 可占位 |
| `canvasStyleData` | **string** | 画布 JSON |
| `componentData` | **string** | 组件数组 JSON |
| `dynamicData` | **string** | `{viewId: ChartView}` |
| `staticResource` | **string** | `{key: dataURL}` |
| `appData` | null | 本技能不生成应用模板 |

## 拆解脚本写出字段清单

`split_atoms.py` 必须从 DET2 算出（不得留空，除非标注 `unknown`）：

1. `source.template_id/name/origin_component_id`
2. `dv_type`
3. `kind` `chart_type` `role`
4. `placement.origin_region` `prefer` `avoid` `hero_ok`
5. `size.*` `area_ratio`
6. `theme`（来自画布背景/主色启发式）
7. `compat.kit`
8. `payload.component/view/resource_keys`
9. 嵌套 `DeTabs.propValue[].componentData` / `Group.propValue` 展平为独立原子，`notes` 记录父组件
