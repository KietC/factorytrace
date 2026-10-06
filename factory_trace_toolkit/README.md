# Factory Trace Toolkit

## English

A portable, evidence-first Python toolkit for tracing the legal manufacturer, actual site, exact SKU, and target process behind a product. Selling a matching item, holding a certificate, or publishing workshop pictures does not establish the source factory.

Keep separate **seller/contracting entity/payee `S` → manufacturer `M` → actual site `L` → exact SKU `K` → target process `P`**. Toolmaking, component forming, assembly, and testing require distinct evidence.

### Installation and requirements

Start with the repository-level [deployment guide](../DEPLOY.md) for ordered installation, optional system tools, skill setup, real smoke tests, and troubleshooting. Python 3.11–3.14 is required. Windows, macOS, and Linux are target platforms: run tests on your environment; a configured CI matrix does not prove all platforms passed.

The deterministic core needs Pillow/jsonschema and no generative model, GPU, CUDA, or API key. Optional reports use openpyxl/python-docx; media uses OpenCV and separately installed system tools; process packs use PyYAML. OCR uses language data, not a required local LLM. External assistants/visual-search services must be logged separately and their output is not production evidence. See [model provenance](MODEL_USAGE_AND_PROVENANCE.md).

Activate the virtual environment or call its executable directly. Cases belong outside this repository. The following paths are placeholders; use your actual quoted paths:

```bash
factorytrace --help
factorytrace doctor --output environment.current.json --model-mode none --strict
factorytrace init "example-case" --root /path/to/private-cases --time-zone "UTC"
```

Keep environment reports private because they may expose local paths. Edit the generated profile/crop plan using actual input; synthetic examples/tests are never evidence.

### Research workflow

```bash
factorytrace ingest /path/to/originals --recursive --case-root CASE --workers 8
factorytrace variants /path/to/preserved.jpg --case-root CASE --crop-plan CASE/work/crop_plan.json
factorytrace queries --profile CASE/work/product_profile.json --case-root CASE
factorytrace validate --case-root CASE
factorytrace materials --case-root CASE --stage discovery
factorytrace ledger --case-root CASE
factorytrace fetch CASE/evidence/url_queue.csv --case-root CASE --workers 8 --per-host 2 --delay 1 --retries 2
factorytrace assess --case-root CASE
factorytrace hypotheses --case-root CASE
factorytrace certification check --scheme watermark --record RECORD.json --target TARGET.json
factorytrace social assess --case-root CASE
factorytrace events validate --case-root CASE
factorytrace report --case-root CASE --format md,json,csv,xlsx,docx
factorytrace lint-report --case-root CASE
factorytrace audit --case-root CASE --stage operational
```

`queries` generates queries for a researcher, not autonomous browser searches. `fetch` captures queued public URLs, not logged-in marketplaces. Certification checks evaluate supplied records and cannot replace official registry evidence. Request only output formats whose optional dependencies are installed.

An `operational PASS` means usable workflow artifacts, not factory identity/purchase suitability. Confirmation requires a real `factorytrace audit --case-root CASE --stage confirmed` pass. It recalculates assessment/hashes/hard gates and requires `S4_BATCH_LINKED`; handwritten grades or percentages cannot bypass the gate.

### Capabilities

- Raw-byte preservation, SHA-256/UTC metadata, concurrent ingestion, locked/atomic manifests.
- Lineage-aware grayscale/crop/logo-neutral/optional mirror derivatives and bilingual query matrices.
- Staged material completeness checks, canonical candidate/claim/evidence validation, execution/model-use provenance.
- Bounded public URL captures with robots checks, retry/backoff, size limits, hashes, and metadata.
- dHash/pixel/edge screening that does not prove shared tooling or identify a factory.
- Separate trace stage, analytic confidence, Evidence Sufficiency Score (ESS), fit, certification, verification priority, and procurement utility.
- WaterMark/UL supplied-record adapters distinguishing holder/listee from manufacturer/site.
- Social evidence bindings: account → entity → site → equipment → process → exact SKU.
- EPCIS-style event validation, process packs, MD/JSON/CSV/XLSX/DOCX reports, semantic lint, and `research → operational → confirmed` audits.

### Documentation

- [Operations](OPERATIONS_MANUAL.md), [dependencies](ENVIRONMENT_AND_DEPENDENCIES.md), [cross-platform notes](CROSS_PLATFORM.md).
- [Data model](CASE_DATA_MODEL.md), [evidence standard](EVIDENCE_STANDARD.md), [schemas](schemas/README.md).
- [Materials](PHOTO_MATERIAL_CHECKLIST.md), [prompts](PROMPTS.md), [execution protocol](PROMPT_EXECUTION_PROTOCOL.md).
- [Iteration/review](SELF_ITERATION.md), [source access](SOURCE_ACCESS_POLICY.md), [troubleshooting](TROUBLESHOOTING.md).
- [Model provenance](MODEL_USAGE_AND_PROVENANCE.md), [portable memory](PORTABLE_MEMORY.md), [portable provenance](PORTABLE_PROVENANCE.md), [research notes](ONLINE_RESEARCH_2026-07-25.md).

### Isolation, access, and licensing

The source distribution excludes real cases, contacts, procurement documents, customer identities, and production conclusions. Migrate old cases into separate copies, then validate/assess/audit; past conclusions do not become current facts automatically.

Use normal authorized browser sessions for login/JavaScript/CAPTCHA/visual search, preserving authorized captures/downloads as case evidence. Do not bypass access controls or rate limits. Ask before uploading confidential material to external services. Keep cookies/tokens/HAR/session data and unredacted cases out of public commits.

See the repository [MIT license](../LICENSE) and [third-party notices](../THIRD_PARTY_NOTICES.md); bundled third-party data retains its own notices.

For a complete public distribution, follow the manifest-driven whole-repository packaging instructions in [CONTRIBUTING.md](../CONTRIBUTING.md) and use [package_public_release.py](../scripts/package_public_release.py). The older toolkit `scripts/package_toolkit.py` exports only this subtree, excluding the repository-level deployment manual and Skill; it is not a complete deployment package.

## 中文

这是一套从产品照片追溯真实制造主体、制造地点、目标工序和精确 SKU 的可迁移工具包。它不会把“卖过同款”“持有证书”“有工厂照片”自动写成“源头厂家”。

核心对象必须分开：

`销售/签约/收款主体 S → 制造责任主体 M → 实际制造地点 L → 精确 SKU K → 具体工序 P`

追“开模厂家”时，`P` 必须绑定真实的模具制造工序。模具制造、零件成形、装配和测试必须分别核验，持证证据不能替代。

## 模型声明

核心工具链是 `core/no-model`：只需要 Python 3.11–3.14、Pillow 和 jsonschema，不需要本地模型、GPU、CUDA或API Key。默认 bootstrap 会装齐报告、媒体、YAML工艺包、FFmpeg、OCR和ExifTool并做真实能力测试；`CoreOnly`仍可完成初始化、校验、评估和基础报告。云端Codex等分析助手与Lens/Bing等外部视觉搜索必须分开记录；两者都只能辅助发现和审查，输出不能直接作为生产证据。

模型使用必须按每个新案件的实际执行日志声明；“没有记录”不能写成“证明从未调用”。详见[模型使用与溯源](MODEL_USAGE_AND_PROVENANCE.md)。

## 快速开始

先按仓库根目录 [部署指南](../DEPLOY.md) 配置依赖、系统工具、Skill 和能力测试。要求 Python 3.11–3.14；代码面向 Windows、macOS、Linux 并处理空格和 Unicode 路径。目标系统仍须运行 `doctor`、能力测试和单元测试；CI 配置矩阵不等于全部平台已实际通过。

### Windows PowerShell

```powershell
cd <factory_trace_toolkit所在目录>
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
.\.venv\Scripts\factorytrace.exe doctor --output .\environment.current.json --model-mode none --strict
.\.venv\Scripts\factorytrace.exe init "example-case" --root "..\..\private-cases" --time-zone "UTC"
```

### macOS / Linux

```bash
cd /path/to/factory_trace_toolkit
bash scripts/bootstrap.sh
.venv/bin/factorytrace doctor --output ./environment.current.json --model-mode none --strict
.venv/bin/factorytrace init "example-case" --root /path/to/private-cases --time-zone "UTC"
```

随后编辑案件中的 `work/product_profile.json` 和 `work/crop_plan.json`：

```bash
factorytrace ingest /path/to/originals --recursive --case-root CASE --workers 8
factorytrace variants /path/to/preserved.jpg --case-root CASE --crop-plan CASE/work/crop_plan.json
factorytrace queries --profile CASE/work/product_profile.json --case-root CASE
factorytrace validate --case-root CASE
factorytrace materials --case-root CASE --stage discovery
factorytrace ledger --case-root CASE
factorytrace fetch CASE/evidence/url_queue.csv --case-root CASE --workers 8 --per-host 2 --delay 1 --retries 2
factorytrace assess --case-root CASE
factorytrace hypotheses --case-root CASE
factorytrace certification check --scheme watermark --record RECORD.json --target TARGET.json
factorytrace social assess --case-root CASE
factorytrace events validate --case-root CASE
factorytrace report --case-root CASE --format md,json,csv,xlsx,docx
factorytrace lint-report --case-root CASE
factorytrace audit --case-root CASE --stage operational
```

`operational PASS`只表示原件、裁片、查询矩阵和工具链可运行，不表示已经找到厂家、候选可信或适合下单。

`queries` 仅生成供研究者执行的查询，不自动搜索。`fetch` 只保存队列中的公开 URL，不抓已登录平台。认证检查评估所提供记录，不能替代官方取证。未激活环境时用虚拟环境中的完整可执行路径；仅请求已安装可选依赖的格式。环境报告可能包含本机路径，应作为私密记录保管。

只有以下命令真实通过，才允许使用“已确认目标工序生产厂家”：

```bash
factorytrace audit --case-root CASE --stage confirmed
```

该审计会重新计算多轴评估、逐文件核对哈希和硬门槛；只有 `S4_BATCH_LINKED` 才可能通过 confirmed，不会相信 CSV 中手填的 `A/5/5` 或人工概率。

## 能力

- 原始照片、视频、PDF和文件按原字节保全，生成 SHA-256、UTC时间和 manifest。
- 支持并发摄取；manifest 使用跨平台锁和 atomic replace，避免并发写坏。
- 生成有 lineage 的整图、灰度、局部裁剪、商标中性遮挡和可选镜像版本。
- 根据尺寸、结构、部件、工艺、证书号和 HS 候选生成中英文搜索矩阵。
- 按P0–P3材料计划检查照片、尺寸、视频、批次和独立闭环是否齐备。
- 从canonical候选JSON生成证据CSV视图，并交叉检查Claim/Evidence引用。
- 自动记录CLI执行；可用`log-model`记录模型ID、prompt、输入输出和hash，且模型输出固定不可作证据。
- 对明确允许访问的公开 URL 做并发证据保存：默认每域名 2 并发、1 秒间隔、重试、Retry-After、大小上限、哈希和元数据。
- 使用 dHash、归一化像素差和边缘叠加做图片初筛；输出明确声明不能据此证明同模。
- 按来源独立性、主体/地点/SKU绑定和反证计算 ESS（Evidence Sufficiency Score），同时独立输出 `trace_stage`、分析置信度、能力适配、认证状态、验证优先级和采购效用。
- WaterMark/UL 适配器强制区分 Licence Holder/Listee 与实际 Manufacturer/authorized site。
- 社媒适配器只按 `账号→主体→地点→设备→工序→目标SKU` 逐级闭合，登录阻断不作缺失证据。
- EPCIS风格事件验证和三套数据驱动工艺包（阀件、金属成形、认证产品）。
- MD/JSON/CSV/XLSX/DOCX统一从标准评估生成，语义lint禁止未校准厂家百分比和无来源联系方式。
- 三阶段自审计：`research → operational → confirmed`。

## 必读文件

- [操作手册](OPERATIONS_MANUAL.md)
- [环境、依赖与最低配置](ENVIRONMENT_AND_DEPENDENCIES.md)
- [模型使用与运行溯源](MODEL_USAGE_AND_PROVENANCE.md)
- [案件数据模型](CASE_DATA_MODEL.md)
- [证据标准](EVIDENCE_STANDARD.md)
- [照片与材料清单](PHOTO_MATERIAL_CHECKLIST.md)
- [提示词库](PROMPTS.md)
- [提示词执行协议](PROMPT_EXECUTION_PROTOCOL.md)
- [自迭代与反方审查](SELF_ITERATION.md)
- [跨平台与并发](CROSS_PLATFORM.md)
- [来源访问与隐私策略](SOURCE_ACCESS_POLICY.md)
- [联网研究来源](ONLINE_RESEARCH_2026-07-25.md)
- [可迁移记忆](PORTABLE_MEMORY.md)
- [便携来源说明](PORTABLE_PROVENANCE.md)
- [故障排查](TROUBLESHOOTING.md)
- [JSON Schema](schemas/README.md)

## 案件隔离与迁移

本源码包不包含真实案件、候选联系人、采购资料或案件结论。示例与测试数据仅用于演示结构，不能带入新案件作为证据。已有案件应通过 `factorytrace migrate --case-root OLD --to 2` 生成源目录之外的副本，再校验、评估和审计。历史结论与手填等级不得自动升级为当前事实。

## 网络边界

`fetch` 只保存用户明确列出的公开 URL，默认尊重 robots.txt。登录态、JavaScript、验证码和平台图片搜索应由正常浏览器完成，再把授权的 HTML、截图、HAR 或下载原件入库。工具不绕过登录、验证码、速率限制或访问控制。保密材料上传外部服务前须询问；cookie、token、HAR 和未脱敏案件不得进入公开提交。

本仓库采用 [MIT 许可](../LICENSE)，第三方数据保留原许可，见 [第三方声明](../THIRD_PARTY_NOTICES.md)。完整公开发布须依 [CONTRIBUTING.md](../CONTRIBUTING.md) 的清单驱动整仓打包流程，使用根目录 [package_public_release.py](../scripts/package_public_release.py)。旧的工具包 `scripts/package_toolkit.py` 仅导出工具包子树，不包含根部署手册与 Skill，不能称为完整部署包。
