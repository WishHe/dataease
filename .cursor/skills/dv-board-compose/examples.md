# Examples

## 从自然语言到 DET2

用户：做一张工厂能耗监控大屏，中间主图，两边指标和排名。

```bash
python3 .cursor/skills/dv-board-compose/scripts/assemble_det2.py \
  --recipe screen-hero-center \
  --name "工厂能耗监控中心"
```

产出 `workspace/out/工厂能耗监控中心-TEMPLATE.DET2`，导入模板管理。

## 摄入市场模板再重组

```bash
python3 .cursor/skills/dv-board-compose/scripts/ingest_market.py --download --limit 10
python3 .cursor/skills/dv-board-compose/scripts/split_atoms.py --replace \
  .cursor/skills/dv-board-compose/workspace/raw \
  .cursor/skills/dv-board-compose/workspace/fixtures
python3 .cursor/skills/dv-board-compose/scripts/assemble_det2.py \
  --recipe screen-hero-center \
  --kit kit-电商运营数据平台-template \
  --name "电商风格重组大屏"
```

## 回归

```bash
python3 .cursor/skills/dv-board-compose/scripts/run_pipeline.py
```

须对三个配方全部 `validate_det2.py` 为 OK。
