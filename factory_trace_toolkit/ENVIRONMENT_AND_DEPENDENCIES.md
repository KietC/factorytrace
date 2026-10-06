# Environment and dependencies / 环境与依赖

## English

### 1. What the repository includes

The source package contains Python code, dependency constraints, schemas, synthetic fixtures, the Agent Skill, four fixed Tesseract language datasets, an OFL-licensed Noto CJK font, and reproducible OCR probes. It does not contain a Python interpreter, virtual environment, browser login, API credential, customer dataset, proprietary font, or external media executable.

The core does not invoke a generative local model. Tesseract uses OCR language data; saying "no LLM required" does not mean OCR has no trained data. Cloud assistants, local enrichment models, and external image-search services are optional and must be logged separately. AI output is not manufacturing evidence.

### 2. Choose an installation tier before running commands

| Tier | Python requirements | External requirements | Capabilities |
|---|---|---|---|
| Core | Python 3.11–3.14, Pillow, jsonschema and transitive dependencies | None | init, ingest, variants, queries, ledger, validation, assessment, ACH, base reports and audits |
| Full Python | Core + openpyxl, python-docx, OpenCV headless, PyYAML | None for Python-only tests | XLSX/DOCX reporting, media/CV adapters and YAML packs |
| Full media | Full Python | FFmpeg/ffprobe, Tesseract, ExifTool | Actual decode, OCR and metadata capability probes |

Full validation scripts import full extras even when external runtime probes are skipped. Do not run them in a core-only environment and interpret missing extras as a core bug.

### 3. Ordered setup

Follow the complete, shell-specific sequence in [the root deployment guide](../DEPLOY.md) and [setup/pitfalls](../docs/SETUP_AND_PITFALLS.md). The order is: select supported Python → create a fresh venv → select its executable explicitly → install pinned installer/build backend → install core or full Python dependencies using constraints → pip check → CLI help/doctor → install the Skill separately → opt in to external tools → verify real capabilities → create a case outside the repository.

Never copy a venv across directories, disks, operating systems or machines. Paths embedded in entry points and pyvenv.cfg may be invalid. Do not upgrade or replace system Python, change global PATH, create network shares, or change browser accounts just to use the core.

### 4. Declared dependency baseline

The declared version range is [pyproject.toml](pyproject.toml). Reproducible version constraints are [constraints-tested.txt](constraints-tested.txt). Version constraints are not a hash lock. Keep normal package index trust protections enabled.

| Package | Pinned version | Role |
|---|---:|---|
| pip | 26.1.2 | Installer |
| setuptools | 83.0.0 | Build backend |
| Pillow | 12.3.0 | Images and deterministic transforms |
| jsonschema | 4.26.0 | Schema validation |
| attrs | 26.1.0 | Schema dependency |
| jsonschema-specifications | 2025.9.1 | Schema registry |
| referencing | 0.37.0 | Reference resolution |
| rpds-py | 2026.6.3 | Reference data structures |
| typing_extensions | 4.16.0 | Typing compatibility |
| openpyxl | 3.1.5 | XLSX |
| et_xmlfile | 2.0.0 | XLSX XML dependency |
| python-docx | 1.2.0 | DOCX |
| lxml | 6.1.1 | DOCX XML dependency |
| numpy | 2.4.6 | CV arrays |
| opencv-python-headless | 4.14.0.94 | CV/media adapters |
| PyYAML | 6.0.3 | Safe YAML packs |

The exact versions above are release dependencies, not a disclosure of a production host. Actual host hardware, OS edition, machine names, mount points and local test receipts are not published.

### 5. Capacity planning, not a benchmark

| Workload | Planning budget | Conservative workers |
|---|---|---|
| Small manual case | 4 logical CPUs, 8 GB RAM, 5 GB free disk | ingest/compare 2; fetch 4, per-host 1, delay 2s |
| Typical image case | 8 CPUs, 16 GB RAM, 20 GB SSD space | ingest/compare 4; fetch 8, per-host 2, delay 1s |
| Larger local batch | 16 CPUs, 32 GB RAM, 50 GB SSD space | local ingest/compare 8; same public-site limits |

These are estimates, not minimum hardware certification or measured throughput. Disk needs depend on originals, lossless derivatives, videos and download limits. Preserve at least a sensible safety margin. More CPU or bandwidth does not authorize higher per-site request rates.

### 6. Cross-platform limits and offline preparation

Python is designed for Windows, macOS and Linux, but each OS/CPU/Python combination needs its own test run. A CI matrix definition is not a passed matrix. macOS Apple Silicon must use arm64 Python/wheels rather than accidentally mixing x86_64 through Rosetta. Linux minimal installations may require python3-venv; musl/Alpine and some ARM combinations may lack a pinned OpenCV wheel. Use core-only or build/audit dependencies yourself; do not claim full support without a successful smoke test.

For offline use, prepare wheels on a matching OS/architecture/Python machine with `pip download --constraint constraints-tested.txt`, transfer them separately, and use `--no-index --find-links`. Also supply the matching build-backend wheel if installation uses an isolated build. Media executables must be provisioned separately. A Windows wheelhouse is not a macOS/Linux wheelhouse.

### 7. OCR reproducibility

The [tessdata manifest](resources/tessdata/MANIFEST.json) binds the fixed Apache-2.0 language data. The [font manifest](resources/fonts/MANIFEST.json) binds the included OFL font. Runtime OCR probes use existing PNGs, so they do not consult a system font. To reproduce probe PNGs with the pinned Pillow version:

```bash
python scripts/generate_ocr_probes.py --font resources/fonts/NotoSansCJKsc-Regular.otf --output-dir resources/ocr_probes
```

Do not substitute another font and call the changed bytes equivalent. OCR only extracts candidate text; retain the source image and manually verify important numbers, certificate IDs and company names.

### 8. Acceptance and rollback

After full Python installation, run unit tests and `verify_toolkit.py --skip-runtime-smoke`. After media tools are available, run full capability and end-to-end verification. Save environment and test outputs outside the repository: they contain local paths and possibly hardware information.

`doctor` checks configuration, not the truth of supplier claims. `operational PASS` means readiness, not confirmed manufacturing. Uninstall by removing this project-specific venv and the Skill copy you installed; do not delete separate case evidence. Do not automatically uninstall shared system tools.

## 中文

### 1. 仓库包含什么

源码包提供 Python 代码、依赖约束、Schema、合成示例、Agent Skill、四份固定 Tesseract 语言数据、OFL 开源 Noto 字体以及可复现 OCR 探针。不提供 Python 解释器、虚拟环境、浏览器登录态、API 凭据、客户数据、私有字体或外部媒体可执行文件。

核心不调用生成式本地模型。Tesseract 仍使用训练过的 OCR 数据；“不需要大语言模型”不等于 OCR 没有模型数据。云端助手、本地辅助模型与外部图片搜索属于可选能力，必须分开留档，AI 回答本身不是生产证据。

### 2. 先选择安装档位

| 档位 | Python 依赖 | 外部依赖 | 可用能力 |
|---|---|---|---|
| 核心 | Python 3.11–3.14、Pillow、jsonschema 及传递依赖 | 无 | 建案、入库、裁片、查询、台账、校验、多轴评估、ACH、基础报告、审计 |
| 完整 Python | 核心 + openpyxl、python-docx、OpenCV headless、PyYAML | Python 单测不需要媒体引擎 | Word/Excel 报告、CV/媒体适配器、YAML 工艺包 |
| 完整媒体 | 完整 Python | FFmpeg/ffprobe、Tesseract、ExifTool | 真实解码、OCR、元数据能力探针 |

完整发布验证脚本即使跳过外部探针，也需要 full Python extras。不要在 core-only 环境跑完整验证，把缺少可选依赖误认成核心故障。

### 3. 按顺序配置

完整、分终端命令见 [根部署手册](../DEPLOY.md) 和 [配置顺序与坑](../docs/SETUP_AND_PITFALLS.md)。顺序固定为：选择支持的 Python → 新建 venv → 明确使用其解释器 → 安装约束版本的安装器/构建后端 → 按 constraints 安装 core 或 full Python 依赖 → pip check → CLI help/doctor → 单独安装 Skill → 按需安装外部工具 → 测真实能力 → 在仓库外创建案件。

不要跨目录、磁盘、系统或机器复制 venv，入口文件与 pyvenv.cfg 的路径可能失效。只为使用核心流程，不需要升级系统 Python、修改全局 PATH、建立网络共享或切换浏览器账号。

### 4. 公开依赖基线

支持范围见 [pyproject.toml](pyproject.toml)，精确版本见 [constraints-tested.txt](constraints-tested.txt)。固定版本不是文件哈希锁；不要关闭正常包源校验。英文区完整列出了 16 个版本；它们是软件发布依赖，不是生产宿主机配置。公开源码不保存真实硬件、系统版本、机器名、挂载点或本机运行回执。

### 5. 资源建议，不是性能承诺

| 工作量 | 规划资源 | 保守并发 |
|---|---|---|
| 小型人工案件 | 4 逻辑核、8 GB RAM、5 GB 空间 | 本地 2；fetch 4、单域 1、间隔 2 秒 |
| 常规图片案件 | 8 核、16 GB RAM、20 GB SSD 空间 | 本地 4；fetch 8、单域 2、间隔 1 秒 |
| 较大本地批次 | 16 核、32 GB RAM、50 GB SSD 空间 | 本地 8；公网单站限制不变 |

这些是估算，不是最低硬件认证或实测吞吐。磁盘按原件、无损派生图、视频与下载上限估算并留余量。核数和带宽更大，不代表可以增加平台单站请求频率。

### 6. 跨平台与离线坑

代码面向三平台，但每个系统/架构/Python 组合必须自己验收；有 CI 矩阵不代表矩阵已通过。Apple Silicon 避免 arm64 与 Rosetta/x86_64 混用；精简 Linux 可能缺 python3-venv；Alpine/musl 或部分 ARM 组合可能没有约束版 OpenCV wheel。必要时用 core-only，或自行构建并审查依赖，不能直接宣称 full 可用。

离线部署需在匹配系统/架构/Python 的机器准备 wheelhouse，使用 `pip download --constraint constraints-tested.txt`，另行传输，并以 `--no-index --find-links` 安装。隔离构建还需构建后端 wheel；媒体引擎单独准备。Windows 的 wheelhouse 不能冒充 macOS/Linux 的。

### 7. OCR 复现

[语言数据清单](resources/tessdata/MANIFEST.json) 固定 Apache-2.0 数据；[字体清单](resources/fonts/MANIFEST.json) 固定随包 OFL 字体。运行时探针读取现成 PNG，不依赖系统字体。重新生成时使用固定 Pillow 与英文区命令；更换字体后产生的新哈希不能宣称与原探针等价。OCR 只能提取线索，关键参数、证书号与主体名称必须看原图人工复核。

### 8. 验收与撤销

full Python 安装后跑单测和 `verify_toolkit.py --skip-runtime-smoke`；媒体引擎就绪后再跑完整能力及端到端测试。环境与测试回执必须落在仓库之外，因为可能包含真实路径与硬件信息。

`doctor` 检查配置，不证明供应商说法真实。`operational PASS` 表示可运行，不是确认制造。撤销只移走本项目 venv 和自己安装的 Skill，保留独立案件原件，不自动卸载其他项目也在用的系统工具。
