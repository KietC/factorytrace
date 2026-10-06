---
name: trace-source-factory
description: Trace the actual source manufacturer, manufacturing site, tooling owner, and target process behind a product using images, dimensions, certification records, official registries, social-media history, trade evidence, factory process evidence, and contradiction analysis. Use for image-led supplier tracing, OEM/ODM and trader-versus-factory separation, WaterMark or UL certificate penetration, mould and process attribution, candidate confidence review, evidence-led supplier reports, and factory-source investigations requiring auditable claims rather than storefront matching.
---

# Source Factory Tracing

## English

### Objective and essential distinctions

Trace the falsifiable claim: **manufacturer `M` performs target process `P` for exact SKU `K` at actual site `L`**. Keep seller/contracting entity/payee `S`, manufacturer `M`, site `L`, SKU `K`, and process `P` separate. Matching images, a brand, a licence holder, trade relationships, assembly capability, or a score does not close this chain. AI output and search summaries are discovery aids, not manufacturing evidence.

The toolkit is deterministic software: no generative model, GPU, or API key is required for its core CLI. Optional OCR uses language data. A research agent/browser supplies external discoveries; the CLI does not autonomously search logged-in marketplaces.

### Intake and CLI

Read original images, specifications, documents, and earlier conclusions. Preserve original bytes and SHA-256, distinguishing originals, derivatives, website captures, and analysis. Specify the target process: tooling, forging, casting, deep drawing, stamping, machining, assembly, calibration, or testing. Unknown dimensions/materials remain unknown.

From this skill directory, run read-only preflight and delegate toolkit arguments after `--`:

```bash
python scripts/preflight_case.py --case-root CASE --stage research
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- --help
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- ingest ORIGINALS --recursive --case-root CASE --workers 8
```

During tracing, read the core CLI, schemas, and output; do not change the toolkit to make a case pass. Store cases outside the source repository. See [deployment instructions](../../DEPLOY.md) in the whole-repository distribution. Installing only this Skill does not copy that repository-level manual or the toolkit; keep the source checkout and pass its toolkit path explicitly with `--toolkit-root`.

### Hypotheses, gates, and material requests

Read [evidence reasoning and ACH](references/evidence-reasoning-ach.md). Write the primary claim with `M/L/K/P`, then test trader, brand owner, licence holder, assembler, component maker, former supplier, and republisher alternatives. Lack of detected contradiction is not confirmation.

Hard gates cover exact model/dimensions/material/structure, identifiable entity/site, direct or strong target-process evidence at that site, officially checked certification scope/status where required, frozen files/provenance/hash, and closure of critical contradictions. Otherwise keep `UNRESOLVED` or `HOLD`.

Use [image and mould fingerprints](references/image-mould-fingerprint.md) and [process evidence](references/process-package.md) to request product views, underside/interfaces, rulers/calipers, disassembled parts, labels/batch codes, manuals, certificates, packing lists, CoC, transaction records, tests, and continuous production video. A pictured logo does not identify a manufacturer without separate evidence.

### Parallel research and browser access

Assign independent lanes and one integrator: images/structure/history; certification; mainland official records; domestic marketplaces; international platforms/social media/trade; process capability; and adversarial review. Prevent concurrent edits to one canonical case file. Deduplicate reposts into source families.

- Certification: [certification-watermark-ul.md](references/certification-watermark-ul.md).
- Mainland records: [china-official-sources.md](references/china-official-sources.md).
- Social/platform research: [social-and-platform-research.md](references/social-and-platform-research.md).
- Browser receipts: [browser-receipts.md](references/browser-receipts.md).

Use normal authorized sessions, visible clicks, and ordinary downloads, with bounded concurrency and retries. Respect access controls and platform rules. Submit public images to external visual-search services only within user authorization; ask before uploading confidential drawings, private images, or customer documents. Record access failures as blocked/unverified, not verified or absent.

### Claims, multi-axis assessment, and confirmation

Create atomic claims and cite only evidence that supports each fact. Record publisher, original URL/title, publication/access times, frozen path/hash, support direction, independence, entity/site/SKU/process bindings, and limitations. Downgrade search pages, reseller pages, marketing claims, summaries, and AI output. Official records, site-bound continuous production evidence, audits, exact-batch transactions/tests, and repeatable fingerprints are stronger, but support only their specific scope.

```bash
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- ledger --case-root CASE
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- validate --case-root CASE
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- assess --case-root CASE
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- hypotheses --case-root CASE
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- report --case-root CASE --format md,json,csv,xlsx,docx
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- lint-report --case-root CASE
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- audit --case-root CASE --stage operational
```

Keep `trace_stage`, `analytic_confidence`, ESS, capability fit, certification status, verification priority, and procurement utility separate. Do not relabel scores as calibrated manufacturer probabilities. Geographic procurement preferences may filter purchasing candidates, not strengthen source attribution. An `operational PASS` means the workflow is usable, not that the factory is confirmed. Say “confirmed manufacturer for the target process” only if `S4_BATCH_LINKED`, the core `confirmed` audit actually passes, all project gates close, and no critical contradiction remains.

### Review and deliverables

Expiry/suspension, entity/site/SKU/BOM/material/tooling changes, test failures, withdrawn evidence, batch-chain conflicts, and new contradictions trigger review. Freeze prior evidence; put affected claims/candidates on `REVIEW_REQUIRED` or `HOLD`; scope impacted SKU/site/batch/process; reverify official status and independent process/transaction evidence; record corrective actions, reviewer, and dates; restore status only after closing the trigger.

Read [report semantics](references/report-semantics.md), then use the [report template](assets/report-template.md) and [inquiry template](assets/inquiry-template.md). Deliver reports/ranked candidates, claims/ledger, source-backed contacts, frozen images/pages and hashes, search/browser receipts including failures, review triggers, and next evidence requests. Distinguish `CONFIRMED`, `SUPPORTED`, `INFERENCE`, `LEAD`, `CONTRADICTED`, and `UNRESOLVED`; every contact needs a source URL and last verification time. Input schemas are in [assets/schemas](assets/schemas/).

## 中文

# 源头厂家溯源

## 执行原则

把任务定义为寻找“精确产品或 SKU 在某一实际地点由某一法律主体完成某一目标工序”的证据链。始终分开记录：

- 销售、签约或收款主体 `S`
- 制造责任主体 `M`
- 实际制造地点 `L`
- 精确产品或 SKU `K`
- 目标工序 `P`

不要用同款图片、品牌、证书持有人、贸易关系、装配能力或概率分数替代 `M + L + K + P` 的闭合证据。把模型输出、搜索摘要和候选评分视为发现线索或推理材料，不视为生产证据。

核心 CLI 是确定性软件，不要求生成式模型、GPU 或 API Key；可选 OCR 使用语言数据。外部发现来自研究人员/代理与浏览器，CLI 不会自动搜索已登录平台。部署顺序见 [DEPLOY.md](../../DEPLOY.md)，案件放在源码仓库之外。

## 开始前

整仓副本的部署手册为 [DEPLOY.md](../../DEPLOY.md)。单独安装 Skill 不会复制该根手册或工具包；保留源码仓库，并通过 `--toolkit-root` 明确指定工具包，不能按安装后 Skill 的父目录猜路径。

1. 读取用户给出的原始图片、参数、目录和历史结论。
2. 保留原件，计算 SHA-256，并区分原始证据、派生图、网页快照和分析产物。
3. 明确目标工序，例如热锻、压铸、深拉、冲压、机加工、模具制造、装配、校准或测试。
4. 运行只读案件预检：

```bash
python scripts/preflight_case.py --case-root CASE --stage research
```

5. 需要调用核心工具链时，使用跨平台包装器并将核心参数置于 `--` 后：

```bash
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- --help
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- ingest ORIGINALS --recursive --case-root CASE --workers 8
```

不要修改核心 `factory_trace_toolkit`。只读取其 CLI、Schema 和输出；把案件数据写入用户指定案件目录。

## 制定问题与闸门

把主假设写成可证伪句子：`候选主体 M 在地点 L 为精确 SKU K 完成目标工序 P`。为每个候选建立替代解释：贸易商、品牌方、持证人、装配厂、零件厂、历史供应商、转售商或图片搬运者。

先读取 [evidence-reasoning-ach.md](references/evidence-reasoning-ach.md)，再建立 ACH 矩阵、反证队列和停止条件。不要把“未发现反证”写成正面确认。

至少设置以下硬门槛：

- 精确型号、尺寸、材质或结构可对应。
- 法律主体与实际地点可识别。
- 目标工序在该地点有直接或强证据。
- 证书状态、型号、主体和地点按官方来源核验。
- 证据文件已冻结，路径、时间、URL 和哈希可复查。
- 关键矛盾已关闭；未关闭时保持 `UNRESOLVED` 或 `HOLD`。

## 获取材料

向用户索取能区分模具和工艺的照片与材料：多角度整机、底面、接口、尺寸标尺、拆件、包装标签、批次码、证书号、说明书、装箱单、CoC、采购记录、测试记录和视频。读取 [image-mould-fingerprint.md](references/image-mould-fingerprint.md) 规划裁剪、无商标搜索和模具指纹；读取 [process-package.md](references/process-package.md) 规划工艺包和现场证据。

不要依据图片中的商标直接归属生产主体，除非用户明确证明商标与制造方有关。

## 并行研究

把研究拆成互斥工作流，并指定单一整合者：

1. 图片和结构：无商标裁剪、尺寸组合、模具指纹、最早发布时间。
2. 认证：证书号、型号、持证人、制造商、制造地点、状态和历史变更。
3. 中国内地官方源：企业登记、环评、排污、技改、招聘、政府公示、法院和知识产权。
4. 国内平台：1688、淘宝、企业官网、公众号、视频号、抖音和地图。
5. 国外平台：Alibaba、LinkedIn、Facebook、YouTube、进口记录和经销网络。
6. 工艺能力：设备、模具、原料、连续工序、质量与测试体系。
7. 反方审查：逐项寻找能推翻领先候选的事实。

按需要读取：

- WaterMark/UL：[certification-watermark-ul.md](references/certification-watermark-ul.md)
- 国内官方源：[china-official-sources.md](references/china-official-sources.md)
- 国内外社媒：[social-and-platform-research.md](references/social-and-platform-research.md)
- 浏览器操作与回执：[browser-receipts.md](references/browser-receipts.md)

友好点击和下载，限制并发与重试，遵守登录、访问控制、robots 和平台规则。浏览器打不开 DOM 时记录真实阻断原因，不要写成“已核验”。

公开图片提交外部识图平台仍需符合用户授权；私密图纸、保密照片和客户文件上传前须询问。同源转载归为一个来源族，不重复加权；并发人员不同时编辑同一规范案件文件。

## 建立证据与主张

把每条事实拆成原子 claim，并使其只引用真正支持该事实的 evidence。记录：来源主体、原始 URL、页面标题、发布时间、获取时间、原始文件、SHA-256、支持方向、独立性、对象绑定、地点绑定、SKU 绑定、工序绑定和限制。

把搜索结果页、转售页面、营销文字、搜索摘要和 AI 输出降级处理。把官方注册表、认证机构记录、政府文件、连续生产视频、带地点和设备身份的审厂材料、订单/提单/CoO、精确批次测试和可重复的模具指纹比对提升为强证据，但仍检查其具体支持范围。

## 多轴评估与确认

使用核心 CLI 校验Schema、重建台账、生成ACH、多轴评估、统一报告和审计：

```bash
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- ledger --case-root CASE
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- validate --case-root CASE
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- assess --case-root CASE
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- hypotheses --case-root CASE
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- report --case-root CASE --format md,json,csv,xlsx,docx
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- lint-report --case-root CASE
python scripts/factorytrace_cli.py --toolkit-root TOOLKIT -- audit --case-root CASE --stage operational
```

固定分开输出 `trace_stage`、`analytic_confidence`、ESS、能力适配、UL/WaterMark状态、验证优先级和采购效用。不要生成未校准的厂家概率，也不要把任一分数改写成统计概率。中国内地只作为采购榜硬过滤，不能提高源头归因。`operational PASS` 只说明流程和案件结构可运行。只有 `trace_stage=S4_BATCH_LINKED`、核心 `confirmed` 审计真实通过、所有项目硬门槛闭合且无关键反证时，才使用“已确认目标工序生产厂家”。

## 失效与复核

出现证书暂停/过期、主体或地点变更、型号/BOM/材质/模具变更、测试失败、网页撤回、批次链冲突、关键证据失效或新反证时：

1. 冻结旧证据，不覆盖原件。
2. 将相关 claim 和候选转为 `REVIEW_REQUIRED` 或 `HOLD`。
3. 限定受影响的型号、地点、批次和工序。
4. 重新核验官方状态、现场工艺和独立交易链。
5. 记录纠正措施、复核日期、复核人和新证据。
6. 只有关闭触发原因后才恢复状态。

## 交付

读取 [report-semantics.md](references/report-semantics.md)，再使用 [report-template.md](assets/report-template.md) 和 [inquiry-template.md](assets/inquiry-template.md)。优先交付：

- 主报告与候选降序表
- 证据台账与 claims
- 联系方式及其证据 URL
- 图片/网页快照和 SHA-256 清单
- 搜索日志、浏览器访问回执和失败原因
- 复核触发器、待询证问题和下一步动作

在报告中显式区分 `CONFIRMED`、`SUPPORTED`、`INFERENCE`、`LEAD`、`CONTRADICTED`、`UNRESOLVED`。分析置信度只描述判断可靠程度；不输出“厂家概率”。所有联系方式必须带来源 URL 和最后核验时间。

## 资源路由

- 设计证据和反证：读取 `references/evidence-reasoning-ach.md`。
- 穿透 WaterMark/UL：读取 `references/certification-watermark-ul.md`。
- 查中国登记、环评和设备能力：读取 `references/china-official-sources.md`。
- 查 LinkedIn、Facebook、Alibaba、1688 等：读取 `references/social-and-platform-research.md`。
- 做图片、模具和结构比对：读取 `references/image-mould-fingerprint.md`。
- 编制设备、模具、工序和测试包：读取 `references/process-package.md`。
- 写多轴结论并检查禁用概率语义：读取 `references/report-semantics.md`。
- 记录浏览器可达性和页面证据：读取 `references/browser-receipts.md`。
- 生成或验证案件输入：使用 `assets/schemas/` 下的 Schema。
