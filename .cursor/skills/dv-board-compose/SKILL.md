---
name: dv-board-compose
description: >-
  Compose a new DataEase dataV screen or dashboard DET2 by splitting market/local
  templates into atoms (charts, KPI cards, decorations, backgrounds), retrieving
  by placement rules, and assembling with layout recipes. Use when the user asks
  to generate 大屏, 仪表板, dataV, dashboard, DET2, or to ingest/split template assets.
---

# Compose DataEase 大屏 / 仪表板

不要从零写 `componentData`。不要整页套用一个模板。用本目录脚本：拆原子 → 按配方填槽 → 导出 `.DET2`。

## 目录

| 路径 | 作用 |
|------|------|
| `reference/taxonomy.md` | kind/role/区位枚举 |
| `reference/schema.md` | Atom / Kit / Recipe / DET2 字段 |
| `recipes/*.json` | 布局配方（坐标写死，模型不现算） |
| `scripts/` | 采集、拆解、组装、校验 |
| `workspace/` | 生成物：fixtures、atoms、catalog、out |

## 生成流程（必须按序）

1. 确认 `dv_type`：`dataV` 或 `dashboard`。二者原子禁止混拼。
2. 选配方：监控/总览偏 `screen-hero-center`；主图在左用 `screen-left-hero`；分析看板用 `dashboard-filter-kpi-main`。
3. 若 `workspace/catalog/atoms.jsonl` 不存在：
   ```bash
   python3 .cursor/skills/dv-board-compose/scripts/run_pipeline.py
   ```
   有官方 `.DET2` 时放入 `workspace/raw/` 后执行 `split_atoms.py --replace`。
   C 位对照 `workspace/screenshots/` 封面由 `pick_canonical_hero` 自动裁定，见 `reference/hero-covers.json`。不要让用户打开抽检清单勾选。
4. 组装：
   ```bash
   python3 .cursor/skills/dv-board-compose/scripts/assemble_det2.py \
     --recipe screen-hero-center --name "工厂能耗监控中心"
   ```
5. 用 `validate_det2.py` 确认 OK。把 `workspace/out/*-TEMPLATE.DET2` 交给用户：模板管理导入，或资源树「从模板新建」。
6. 只改标题/名称；**不要**改网格坐标、不要跨主题硬拼装饰、不要把 KPI 拉成 C 位。

## 禁令

- 禁止让模型直接输出完整 `canvasStyleData` / `componentData` / `dynamicData`
- 禁止 `hero_ok=false` 的原子进入 `role=hero`
- 模板里用大图拼的 C 位必须进 hero 槽，不要当成背景丢掉；小装饰图仍不进内容槽
- 禁止大屏装饰与浅色仪表板卡片混用
- 本技能只出样式模板（`nodeType=template`），不生成 `.DET2APP`

## 入库（模板工程）

1. `ingest_market.py --download --limit 24` 拉 STYLE `.DET2`
2. 将完整模板放入 `workspace/raw/`
3. `split_atoms.py --replace` 写出原子；`review_heroes.py` 对照封面裁定写出 `hero-review.md`（不一致则非 0 退出）
4. `run_pipeline.py` 夹具回归须全绿

检索时读 `catalog/atoms.jsonl`（无 payload）。完整切片在 `workspace/atoms/<id>.json`。
