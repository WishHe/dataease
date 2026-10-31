# Taxonomy

拆解与组装共用这套枚举。脚本只认下列值；新增取值先改脚本再改文档。

## dv_type

| 值 | 含义 | 布局 |
|----|------|------|
| `dataV` | 数据大屏 | 绝对坐标 `style.left/top/width/height`，默认 1920×1080 |
| `dashboard` | 仪表板 | 网格 `x/y/sizeX/sizeY`，画布 72×36 |

禁止跨 `dv_type` 混拼原子。

## kind

组件切片类型：

| 值 | 来源（典型） |
|----|----------------|
| `chart` | `UserView` 常规图 |
| `kpi` | `indicator` / `gauge` / `liquid` / `indicator-hold` |
| `table` | `table-*` |
| `map` | `map` / `bubble-map` / `flow-map` |
| `query` | `VQuery` |
| `deco` | `DeDecoration` / `CanvasBoard` / `CanvasIcon` / `DynamicBackground`（非满幅） |
| `bg` | 铺满画布的底图 / `DynamicBackground`（面积 ≥85% 或四边贴齐） |
| `title` | `ScrollText` / 标题向文本 / 宽扁顶栏文字 |
| `media` | `Picture` 等：大图可当 C 位，细长条/小图标当皮肤 |
| `shape` | `RectShape` / `CircleShape` / `SvgTriangle` |
| `clock` | `DeTimeClock` |

## role

槽位职责，组装时按 role 检索：

| 值 | 含义 |
|----|------|
| `hero` | C 位主视觉 |
| `kpi` | 指标卡 |
| `support` | 侧图、辅图、排名 |
| `filter` | 查询组件 |
| `header` | 顶栏标题/时间 |
| `footer` | 底栏趋势/滚动 |
| `bg` | 背景 |
| `deco-corner` | 四角装饰 |
| `deco-border` | 边框/分隔 |
| `kit-skin` | 仅随套件复制，不单独检索 |

## placement.origin_region / slot.region

3×3 区位：`top-left` `top` `top-right` `left` `center` `right` `bottom-left` `bottom` `bottom-right`。另允许 `full`、`top-row`、`bottom-row`。

## hero_ok

仅 `true` 的原子可进入 `role=hero` 槽。每个套件 **只有一个** `role=hero`（`pick_canonical_hero`，对照市场封面）：

- 有地图 → 地图为 C 位；除非另有明显更大的 3D/场景 `Picture`（≥1.5 倍）
- 否则大图（面积 ≥12%、长宽比约 0.55–2.8，非满幅底/细长条/四角）为 C 位
- Group 里的地球/光球：按整组面积判断，不要拆成小装饰
- 仪表板 Tab 子组件用父 Tab 格子算面积，且只认第一个 Tab
- 大屏 C 位若是画布 `background` 鸟瞰/场景图（没有地图、也没有大 Picture），合成一张可检索的 `Picture`
- 否则取最大图；再否则取占视觉主导的表
- kpi、四角装饰、顶栏文字、图标级小图 → `hero_ok=false`

## theme

粗标签，用于套件绑定，不是精确色值：`dark-cyan` `dark-blue` `dark` `light` `unknown`。

同板内容原子优先同一 `kit`；跨 kit 仅允许 `theme` 相同且不含对方 `deco`。
