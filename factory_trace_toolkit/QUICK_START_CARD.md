# Quick-start card

## English

Use the root deployment guide to create a venv and select its executable; install core first or full extras when needed. Install the Skill through the explicit installer, keeping existing versions intact. Initialize a case outside this repository, replace every synthetic profile field, ingest originals, generate reviewed variants/queries and acquire sources through allowed channels. Build atomic claims and structured candidates, then run ledger → validate → assess → hypotheses → report → lint-report → audit. Missing material and confirmation gates are valid failures, not install errors. Never fix a failing case by typing a higher score or changing CSV labels.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 一页执行卡

## 环境

```bash
factorytrace doctor --output environment.current.json --model-mode none --strict
```

核心无模型、无GPU；如使用Codex/API改为`cloud`并记录model ID。Lens/Bing等用`--external-visual-service`单独记录。

## 开案

```bash
factorytrace init CASE --root ./cases
factorytrace ingest ./原始材料 --recursive --case-root ./cases/CASE
```

## 先索取

- P0：原始全分辨率图、原始来源、型号/尺寸/部件边界至少一项；
- 原始未压缩整图、底面、四侧、四个45°；
- 尺寸、孔位、R角、翻边、板厚、重量；
- 盖板、阀头、止回阀、弯头拆解；
- 外箱六面、标签、条码、批次、说明书；
- 合同/收款/制造主体；
- 准确厂址、设备、模具和连续生产视频；
- 工单、QC、PO、发票、packing list、COO、证书scope。

## 搜索

1. 整图 + 无商标主体；
2. 底面双孔；
3. R角/翻边；
4. 冲孔盖板；
5. 阀头；
6. 包装/型号；
7. 尺寸 + 品类；
8. 部件 + 开模/深拉/冲压/修边。

## 必拆对象

`S销售/收款 · M制造法人 · L制造地点 · K精确SKU · P目标工序`

## 绝不自动等同

- 商标 ≠ 厂家
- 店铺 ≠ 工厂
- Licence Holder ≠ Manufacturer
- Shipper ≠ Producer
- 有设备 ≠ 做目标SKU
- 装配 ≠ 开模/深拉
- 未搜到 ≠ 不存在

## 三轮

`Researcher → Skeptic → Reconciler`

## 发布前

```bash
factorytrace ledger --case-root CASE
factorytrace validate --case-root CASE
factorytrace assess --case-root CASE
factorytrace hypotheses --case-root CASE
factorytrace report --case-root CASE --format md,json,csv,xlsx,docx
factorytrace lint-report --case-root CASE
factorytrace audit --case-root CASE --stage research
factorytrace audit --case-root CASE --stage operational
factorytrace audit --case-root CASE --stage confirmed
```

`research PASS` 只表示资料结构可研究，`operational PASS` 只表示生产级预处理门槛齐备；只有 `S4_BATCH_LINKED + confirmed PASS` 才允许写“已确认目标工序生产厂家”。任一门槛未 PASS：只能写候选、当前证据和缺口。
