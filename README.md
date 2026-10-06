# FactoryTrace — Evidence-First Manufacturer Tracing

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11–3.14](https://img.shields.io/badge/Python-3.11%E2%80%933.14-blue.svg)](factory_trace_toolkit/pyproject.toml)

[English](#english) · [中文](#中文)

## English

Trace the **actual manufacturer, production site, tooling owner, and target process** behind a product—not merely the storefront selling a similar image.

FactoryTrace combines a local Python toolkit with a reusable agent Skill. It preserves source artifacts, structures claims and contradictions, checks product/site/certification bindings, and generates auditable reports. It is a research workflow and evidence organizer, not a factory database or an automatic supplier-confirmation engine.

### Contents

- [Capabilities](#capabilities)
- [Quick start](#quick-start)
- [Requirements](#requirements)
- [Workflow](#workflow)
- [Repository map](#repository-map)
- [Documentation](#documentation)
- [Validation and support](#validation-and-support)
- [Privacy and licensing](#privacy-and-licensing)

### Capabilities

| Capability | Purpose |
| --- | --- |
| Original-file ingestion and SHA-256 manifests | Preserve what was actually received |
| Brand-neutral crops, masks, queries, and visual comparison | Find leads without treating logos or similarity as supplier proof |
| Entity, site, SKU, process, and batch separation | Avoid confusing trader, licence holder, assembler, and source factory |
| Certification adapters | Check exact-product and authorized-site bindings for WaterMark, UL, or generic records |
| Social-media and production-event assessment | Evaluate public account/site/process connections and batch continuity |
| Multi-axis assessments and contradiction review | Distinguish product match, capability, source attribution, and purchasing fit |
| Markdown, JSON, CSV, Excel, and Word reports | Share evidence with explicit limitations and links |
| Agent Skill with preflight and templates | Reuse the procedure in a compatible agent environment |

It does **not** turn a manually entered percentage into a calibrated probability. A high visual-match score or operational PASS does **not** confirm a manufacturer. Buyer location preferences do not strengthen attribution evidence.

### Quick start

Read [DEPLOY.md](DEPLOY.md) in order for prerequisites, expected results, failure recovery, full media support, Skill installation, and a first case. Use [Setup and pitfalls](docs/SETUP_AND_PITFALLS.md) when a checkpoint fails.

Shortest core installation, from the repository root:

Windows PowerShell:

```powershell
git clone https://github.com/KietC/factorytrace.git
Set-Location -LiteralPath .\factorytrace
py -3.13 -m venv .\factory_trace_toolkit\.venv
$ToolkitPython = (Resolve-Path .\factory_trace_toolkit\.venv\Scripts\python.exe).Path
& $ToolkitPython -m pip install --upgrade pip
& $ToolkitPython -m pip install -e .\factory_trace_toolkit
& $ToolkitPython -m factorytrace --help
```

macOS / Linux:

```bash
git clone https://github.com/KietC/factorytrace.git
cd factorytrace
python3 -c 'import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version'
python3 -m venv factory_trace_toolkit/.venv
TOOLKIT_PYTHON="$PWD/factory_trace_toolkit/.venv/bin/python"
"$TOOLKIT_PYTHON" -m pip install --upgrade pip
"$TOOLKIT_PYTHON" -m pip install -e ./factory_trace_toolkit
"$TOOLKIT_PYTHON" -m factorytrace --help
```

Expected: CLI help includes `init`, `ingest`, `assess`, `report`, and `audit`. Stop on errors; do not silently run another global `factorytrace` command. Cases and private environment receipts belong **outside this repository**.

### Requirements

Package metadata declares Python **3.11–3.14**. A GPU, CUDA, local language model, generative-model API key, or paid search account is **not required by the core CLI**. An agent application and its model/account are separate optional dependencies for assisted research.

| Tier | Python packages | Separate system tools |
| --- | --- | --- |
| Core | Pillow, jsonschema | None for core case/evidence operations |
| Reports | Core + openpyxl, python-docx | None for file generation; rendering is a separate optional workflow |
| Media | Core + opencv-python-headless | FFmpeg/ffprobe, Tesseract, ExifTool for relevant media operations |
| Process packs | Core + PyYAML | None for pack parsing |
| Full | All package extras | Media tools still need separate installation and probes |

Tesseract language data is OCR data, not a local generative model. `pip install ...[full]` does not install operating-system executables. See [Environment and dependencies](factory_trace_toolkit/ENVIRONMENT_AND_DEPENDENCIES.md).

Planning baseline: 4 CPU cores, 8 GB RAM, 5 GB free storage for small cases; 8 cores, 16 GB RAM, 20 GB storage are more comfortable for media work. These are capacity suggestions, not universally measured performance or hard minimum guarantees.

### Workflow

1. Create a case outside the source repository; collect originals, dimensions, material, ratings, markings, and requested processes.
2. Ingest originals and create search variants with recorded lineage.
3. Search independent sources; use normal authorized browser interaction for logged-in platforms. Save URLs, dates, access status, and original evidence.
4. Separate selling/contracting party, payment party, manufacturer, physical site, exact SKU/revision, tooling/process, and batch.
5. Cross-check official certifications, company records, production evidence, social history, and trade/batch documents where available.
6. Validate records, regenerate assessments, review alternative explanations, generate reports, and run semantic/audit checks.
7. Leave unsupported conclusions unconfirmed and state the next evidence needed.

The toolkit generates queries and processes saved evidence; it does not automatically log into platforms, obtain private audit files, contact suppliers, or crawl all social media. Search/browser connectors, accounts, and human decisions remain external. A blocked page means **not verified**, not **no product/factory exists**.

### Repository map

```text
factorytrace/
├── README.md                       # Project entry point
├── DEPLOY.md                       # Ordered deployment and first case
├── docs/                           # Pitfalls, research, publication review
├── scripts/                        # Repository-level deployment helpers
├── factory_trace_toolkit/
│   ├── src/factorytrace/            # Python CLI and evidence logic
│   ├── schemas/                    # Structured record contracts
│   ├── templates/                  # Blank/synthetic templates
│   ├── process_packs/              # Data-driven process requirements
│   ├── resources/                  # Licensed OCR resources and probes
│   ├── scripts/                    # Installation, verification, packaging
│   └── tests/                      # Regression and integration tests
└── skills/trace-source-factory/     # Skill, references, preflight
```

### Documentation

| Read when | Document |
| --- | --- |
| Deploying on a new machine | [Ordered deployment](DEPLOY.md) |
| Troubleshooting setup or research | [Setup and pitfalls](docs/SETUP_AND_PITFALLS.md) |
| Understanding README design choices | [README style research](docs/README_STYLE_RESEARCH.md) |
| Checking publication boundaries | [Public release audit](docs/PUBLIC_RELEASE_AUDIT.md) |
| Preparing photographs/documents | [Photo/material checklist](factory_trace_toolkit/PHOTO_MATERIAL_CHECKLIST.md) |
| Running an investigation | [Operations manual](factory_trace_toolkit/OPERATIONS_MANUAL.md) |
| Understanding accepted evidence | [Evidence standard](factory_trace_toolkit/EVIDENCE_STANDARD.md) |
| Understanding structured data | [Case data model](factory_trace_toolkit/CASE_DATA_MODEL.md) |
| Reading implementation entry points | [Core code guide](docs/CODE_GUIDE.md) |
| Recording model usage | [Model usage and provenance](factory_trace_toolkit/MODEL_USAGE_AND_PROVENANCE.md) |
| Contributing | [Contributing](CONTRIBUTING.md) |
| Handling vulnerabilities/disclosure | [Security](SECURITY.md) |
| Checking licences | [MIT](LICENSE), [third-party notices](THIRD_PARTY_NOTICES.md) |

### Validation and support

The source includes a manual GitHub Actions workflow. Select **Actions → manual-cross-platform-validation → Run workflow** when desired; a matrix definition is not evidence that every OS/Python combination has passed. Do not infer macOS/Linux success from a Windows test.

Core readiness: supported interpreter, successful installation, CLI help, and `pip check`. Full validation additionally needs full extras, unit tests, external probes, capability smoke, and release verification. See [deployment checkpoints](DEPLOY.md#7-validation-checkpoints).

Use [Issues](https://github.com/KietC/factorytrace/issues) for reproducible non-sensitive bugs/features. Include versions, command, expected/actual behavior, and a synthetic minimal input. Do not attach real cases.

### Privacy and licensing

This public source distribution is intended to contain code, generic procedures, blank/synthetic examples, tests, and licensed resources—not production cases, real customer/supplier contact books, company-specific operating details, browser sessions, API secrets, VM credentials, or local environment snapshots. Review modified copies before publishing: `.gitignore` does not remove secrets or untrack previously committed files.

Project-owned code and documentation use [MIT](LICENSE). Third-party assets/dependencies retain their own licences; see [third-party notices](THIRD_PARTY_NOTICES.md). Opening code does not grant rights to a user's data or third-party commercial media. No real supplier relationship or certification claim is implied by a template/test.

---

## 中文

追溯产品背后的**真实制造主体、生产地点、模具责任方与目标工序**，而不只是找到售卖相似图片的店铺。

FactoryTrace 由本地 Python 工具包与可复用 Agent Skill 组成：保留原件、结构化主张与矛盾、核验产品/地点/认证关联，并生成可审查报告。它是研究流程和证据整理工具，不是厂家数据库，也不是自动确认供应商的引擎。

### 功能

| 能力 | 用途 |
| --- | --- |
| 原件归档与 SHA-256 清单 | 保留实际收到的材料 |
| 去品牌裁剪、遮挡、查询与图像比对 | 找线索，不把商标或相似外观当成供货证明 |
| 主体、地点、SKU、工序与批次分离 | 防止混淆贸易商、持证人、装配厂与源头厂 |
| 认证适配器 | 对 WaterMark、UL、通用记录核验精确产品与获准地点 |
| 社媒与生产事件分析 | 检查公开账号、地点、工序关联及批次连续性 |
| 多轴评估与矛盾审查 | 分开产品匹配、生产能力、源头归属与采购适配 |
| Markdown、JSON、CSV、Excel、Word | 保留证据链接和限制条件 |
| Agent Skill、预检与模板 | 在兼容 Agent 环境中复用调查方法 |

工具**不会**把手工百分比变成经过校准的概率。图片相似度高或运行审计通过，**不等于**厂家已确认；采购地区偏好也不能增强源头归属证据。

### 快速开始

按顺序看 [DEPLOY.md](DEPLOY.md)，含前置条件、预期结果、失败恢复、完整媒体能力、Skill 和首案。检查点失败查 [配置顺序与踩坑](docs/SETUP_AND_PITFALLS.md)。

最短 core 安装如下，命令从仓库根目录执行。

Windows PowerShell：

```powershell
git clone https://github.com/KietC/factorytrace.git
Set-Location -LiteralPath .\factorytrace
py -3.13 -m venv .\factory_trace_toolkit\.venv
$ToolkitPython = (Resolve-Path .\factory_trace_toolkit\.venv\Scripts\python.exe).Path
& $ToolkitPython -m pip install --upgrade pip
& $ToolkitPython -m pip install -e .\factory_trace_toolkit
& $ToolkitPython -m factorytrace --help
```

macOS / Linux：

```bash
git clone https://github.com/KietC/factorytrace.git
cd factorytrace
python3 -c 'import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version'
python3 -m venv factory_trace_toolkit/.venv
TOOLKIT_PYTHON="$PWD/factory_trace_toolkit/.venv/bin/python"
"$TOOLKIT_PYTHON" -m pip install --upgrade pip
"$TOOLKIT_PYTHON" -m pip install -e ./factory_trace_toolkit
"$TOOLKIT_PYTHON" -m factorytrace --help
```

预期帮助有 `init`、`ingest`、`assess`、`report`、`audit`。报错先停，不要换用未知全局同名命令。案件和私有环境回执必须在**本仓库外**。

### 环境与依赖

包声明 Python **3.11–3.14**。核心 CLI **不要求** GPU、CUDA、本地大模型、生成模型 API Key 或付费搜索账号；辅助研究的 Agent 应用与模型/账号是独立可选依赖。

| 层级 | Python 依赖 | 另装系统工具 |
| --- | --- | --- |
| Core | Pillow、jsonschema | 核心案件/证据操作无需 |
| Reports | Core + openpyxl、python-docx | 生成无需；渲染属独立可选流程 |
| Media | Core + opencv-python-headless | 相应操作要 FFmpeg/ffprobe、Tesseract、ExifTool |
| Process packs | Core + PyYAML | 解析工艺包无需 |
| Full | 所有 extras | 媒体系统工具仍要另装、核验 |

Tesseract 语言数据是 OCR 数据，不是生成模型；`pip install ...[full]` 不装系统程序。见 [环境与依赖](factory_trace_toolkit/ENVIRONMENT_AND_DEPENDENCIES.md)。

小案件按 4 核、8 GB RAM、5 GB 磁盘规划；媒体更适合 8 核、16 GB、20 GB。只是容量建议，不是普适实测性能或硬性最低保证。

### 流程

1. 仓库外创建案件，收原始图片、尺寸、材质、额定参数、标记和目标工序。
2. 原件入库哈希，生成有来源链的搜索变体。
3. 多源搜索；登录平台用正常已授权浏览器交互，保存网址、日期、访问状态与原件。
4. 分离销售/签约、收款、制造主体、实际地点、精确 SKU/版本、模具/工序和批次。
5. 交叉核验认证、公司登记、生产证据、社媒历史、贸易/批次文件。
6. 校验数据、重评估、审查其他解释、出报告，再执行语义与审计检查。
7. 缺证据保持未确认，列明下一步所需。

工具生成查询、处理已保存证据，不自动登录、取得保密审厂资料、联系供应商或全量抓社媒。搜索/浏览器连接器、账号与人工判断在工具包之外。阻断意味着**未核实**，不是**没有产品/工厂**。

### 仓库结构

```text
factorytrace/
├── README.md                       # 项目入口
├── DEPLOY.md                       # 有序部署与首案
├── docs/                           # 踩坑、研究、公开发布审查
├── scripts/                        # 仓库级部署工具
├── factory_trace_toolkit/
│   ├── src/factorytrace/            # Python CLI 与证据逻辑
│   ├── schemas/                    # 结构化记录约束
│   ├── templates/                  # 空白/合成示例
│   ├── process_packs/              # 工艺要求
│   ├── resources/                  # 授权 OCR 资源与探针
│   ├── scripts/                    # 安装、验证、打包
│   └── tests/                      # 回归与集成测试
└── skills/trace-source-factory/     # Skill、参考、预检
```

### 文档

| 场景 | 文档 |
| --- | --- |
| 新机器部署 | [完整部署顺序](DEPLOY.md) |
| 配置或调查卡住 | [配置顺序与踩坑](docs/SETUP_AND_PITFALLS.md) |
| README 格式依据 | [格式研究](docs/README_STYLE_RESEARCH.md) |
| 公开发布边界 | [公开发布审查](docs/PUBLIC_RELEASE_AUDIT.md) |
| 照片和材料 | [材料清单](factory_trace_toolkit/PHOTO_MATERIAL_CHECKLIST.md) |
| 调查操作 | [操作手册](factory_trace_toolkit/OPERATIONS_MANUAL.md) |
| 证据规则 | [证据标准](factory_trace_toolkit/EVIDENCE_STANDARD.md) |
| 数据结构 | [案件数据模型](factory_trace_toolkit/CASE_DATA_MODEL.md) |
| 阅读实现入口 | [核心代码导航](docs/CODE_GUIDE.md) |
| 模型记录 | [模型使用与来源](factory_trace_toolkit/MODEL_USAGE_AND_PROVENANCE.md) |
| 贡献代码 | [贡献指南](CONTRIBUTING.md) |
| 漏洞/泄露 | [安全说明](SECURITY.md) |
| 许可证 | [MIT](LICENSE)、[第三方声明](THIRD_PARTY_NOTICES.md) |

### 验证与支持

GitHub Actions 为手动工作流，需要时选 **Actions → manual-cross-platform-validation → Run workflow**。定义了矩阵不代表各系统/Python 已通过；Windows 通过也不能代表 macOS/Linux。

Core 就绪标准：解释器受支持、安装成功、CLI 帮助与 `pip check` 正常。Full 还要全 Python 依赖、单元测试、外部探测、能力测试、发布校验，见 [部署验收](DEPLOY.md)。

通过 [Issues](https://github.com/KietC/factorytrace/issues) 提交可复现非敏感问题，附版本、命令、预期/实际结果和最小合成输入，不附真实案件。

### 隐私与许可

公开版只应含代码、通用方法、空白/合成示例、测试与授权资源，不含生产案件、真实客户/供应商联系人、公司操作特征、浏览器登录态、API 密钥、VM 凭据或本机快照。修改后再发布必须复审；`.gitignore` 不会删密钥，也不取消历史已提交文件追踪。

自有代码/文档按 [MIT](LICENSE) 开源，第三方保留各自许可，见 [第三方声明](THIRD_PARTY_NOTICES.md)。开源代码不授权公开用户数据或第三方商业图片；模板/测试不暗示真实供应关系或认证结论。
