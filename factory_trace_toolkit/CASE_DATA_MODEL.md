# Case data model

## English

Represent each manufacturing claim as legal entity, time, physical site, process, product/revision and batch. Candidate JSON is canonical; ledgers, rankings, Markdown, Excel and Word are views, not independent truth. Keep seller, contracting/payment party, exporter, licence holder, assembler, component maker and tooling maker separate. Claims must reference existing evidence IDs; IDs are globally unique within a case. Freeze direct evidence with paths and SHA-256, and reconcile ledger fields with candidate evidence. A single reconciler merges independent research lanes. Rebuild the ledger after changing canonical JSON and run validation/audit. Do not hand-edit a CSV to force a confirmation. Operational readiness is not manufacturer verification; superseded conclusions remain historical.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 案件数据模型与唯一真值

## Schema v2 的原子制造主张

每个结论统一表示为 `法律实体 E 在时间 T 于制造地点 S，执行工艺 P，生产产品/部件/批次 V`，并同时指出：

1. **角色**：seller、contracting entity、payment entity、exporter、licence holder、legal manufacturer、assembler、component maker、tooling maker；
2. **部件**：盘体、盖板、阀头、止回阀、模具或整机；
3. **地点/工序**：准确物理地点以及tooling、deep_draw、punching、welding、assembly等。

“A是厂家”不是合格命题。合格示例：

```text
CL-014: Company A at Site B performed deep drawing of tray body
for SKU K revision R batch X during period T.
```

## Canonical与派生文件

当前版本采用：

| 数据 | Canonical | 派生/索引 |
|---|---|---|
| 候选及评分证据 | `candidates/CAND-*.json`中的`evidence` | `evidence/evidence_register.csv`、排名和报告 |
| Claim | `claims.jsonl` | 报告中的文字结论 |
| 原件 | `artifacts/original/` + `manifest.json` | 裁片、OCR、标注、网页截图 |
| 当前状态 | `case.json.status` + 最新审计 | `STATUS.md`可读摘要 |
| 联系方式 | `evidence/contacts.csv` | 候选表/最终报告 |
| 模型与工具 | `logs/model_usage_log.csv`、`logs/execution_log.csv` | 环境摘要 |
| 主体/场址/证书/事件/社媒 | `evidence/structured/*.json` 与候选内嵌对象 | 适配器结果和报告 |
| 标准评估 | 候选JSON重新计算 | `output/assessments/*.assessment.v2.json` |

CSV不允许手填“A/confirmed”或百分比覆盖候选JSON和审计器。任何CSV、Excel、Word或Markdown报告都是同一标准评估的视图，不能成为第二套真值。

候选JSON修改后重新生成CSV视图：

```bash
factorytrace ledger --case-root CASE
```

不要同时手改candidate evidence和`evidence_register.csv`。audit会阻断confirmed阶段的缺行、孤儿和字段冲突。

## 引用完整性

- `claim.source_ids[]`必须指向存在的`evidence_id`；
- `evidence.claim_id`必须指向存在的`claim_id`，或明确留空为未归类线索；
- 全案`evidence_id`唯一；
- `candidate_id`、`claim_id`、`contact_id`不可复用；
- direct/strong证据必须有冻结的`local_path`和SHA-256；
- ledger与candidate中同ID的URL、哈希、stance、strength、group和process不得冲突；
- confirmed前不得有孤儿Claim、孤儿Evidence或critical open contradiction。

`factorytrace audit`会检查能自动检查的引用与冲突；无法自动判断的语义关系仍由Reconciler审核。

## 单写入者原则

并行搜索线程、代理和人工研究员只能写独立泳道结果。Canonical文件由单一Reconciler合并，避免：

- 两个进程同时改候选JSON；
- 同一个evidence ID指向不同文件；
- 旧报告覆盖新反证；
- 同源转载被当成独立证据。

## 状态含义

- `open/research`：正在收集候选；
- `operational`：原件、裁片、查询矩阵和工具链可运行，不代表已有厂家证据；
- `confirmed`：必须由最新confirmed审计生成；
- `superseded`：结论已被新事实覆盖，保留历史但不得引用为当前状态。

`operational PASS`绝不等于“候选厂家已核实”或“适合下单”。
