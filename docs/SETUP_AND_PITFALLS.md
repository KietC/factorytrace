# Setup Order and Pitfall Register

[English](#english) · [中文](#中文) · [Deployment](../DEPLOY.md)

## English

This is a failure-oriented companion to the ordered [deployment guide](../DEPLOY.md). It does not claim all listed platforms have been tested. Use the same explicitly chosen venv interpreter at every step.

### Required order and stop conditions

| Order | Do this | Pass condition | Stop if |
| --- | --- | --- | --- |
| 1 | Select Python; inspect its actual executable/version | Standard Python 3.11–3.14 | Wrong version, unexpected alias, experimental ABI |
| 2 | Clone/extract source and inspect root | README + `factory_trace_toolkit` + `skills` present | Running in ZIP viewer or wrong nested directory |
| 3 | Create a fresh local venv | Interpreter path points into the intended venv | Old/moved/copied venv or wrong interpreter |
| 4 | Install core and run `pip check`/CLI help | No broken requirements; commands load | Build/download/import error |
| 5 | Create external cases/checks folders | Outputs outside source tree | Production data would be written into Git |
| 6 | Add full Python extras, if needed | Office/OpenCV/YAML imports succeed | Optional package missing or incompatible wheel |
| 7 | Install/probe external tools, if needed | FFmpeg + ffprobe + Tesseract + ExifTool versions | An executable cannot run |
| 8 | Check OCR languages and capability smoke | Bundled language list and actual round trips | Engine found but unusable languages/media/fonts |
| 9 | Install Skill into one verified location | Skill visible and wrapper points to toolkit | Duplicate/conflicting Skill or wrong root |
| 10 | Create demo case and basic report | Valid outputs, no unsupported confirmation | Schema/template/path mismatch |
| 11 | Authenticate browser/search separately | Intended page and saved receipt work | Login/CAPTCHA/connector restrictions |
| 12 | Begin real research, review before publication | Evidence lineage and privacy review | False certainty, duplicate evidence, sensitive artifacts |

### Environment pitfalls

| Symptom | Likely cause / diagnostic | Safe resolution |
| --- | --- | --- |
| `py -3.13` not found | No runtime/launcher or different launcher generation | Install supported Python officially, reopen terminal; use an explicit interpreter path |
| Store opens when running `python` | App execution alias rather than intended Python | Do not change global settings blindly; invoke the installed executable directly |
| Python assertion fails | Interpreter outside 3.11–3.14 | Choose supported version before creating venv; do not change system Python symlinks |
| `ensurepip`/venv unavailable on Linux | Distribution splits venv package | Install the corresponding supported `pythonX.Y-venv` package; retry with same interpreter |
| `externally-managed-environment` | Installing into system Python | Create/use venv; do not use `--break-system-packages` |
| `Activate.ps1` denied | PowerShell script policy | Use `.venv\Scripts\python.exe` directly; no global policy change needed |
| `UnicodeDecodeError: gbk` in a third-party validation script | Script opens bilingual files without specifying UTF-8 | Run that command with `python -X utf8` (or a process-local `PYTHONUTF8=1`); do not change the machine locale |
| `No module named factorytrace` | Wrong interpreter or toolkit not installed | Print `sys.executable`; run that interpreter's `-m pip install -e` on toolkit directory |
| Shell cannot find `factorytrace` | Unactivated environment/PATH | Use the intended venv interpreter with `-m factorytrace` |
| pip cannot find a pinned release/wheel | Exact snapshot mismatch, mirror lag, Python/architecture incompatibility | Check error and metadata; try allowed ranges without historic constraints, record versions; never disable TLS |
| Package build requires a compiler | No compatible wheel for selected ABI/architecture | Use standard supported Python and platform build prerequisites only if needed; do not assume binary wheels everywhere |
| `docx` or `cv2` import fails | Reports/media extras absent or wrong import/distribution name | Install `[reports]`/`[media]`/`[full]`; distribution `python-docx` imports `docx`, OpenCV imports `cv2` |
| Unix `[full]` behaves strangely | Unquoted shell glob | Quote the whole install target including `[full]` |
| `ffmpeg` exists but video check fails | `ffprobe` missing, broken codec or executable | Probe both FFmpeg and ffprobe, then use capability smoke to isolate round-trip failure |
| Installed Windows tools not found | Current shell has stale PATH or package installed elsewhere | Open a new shell; inspect `Get-Command`; do not install conflicting duplicates |
| Winget package ID disappears | Catalogue ID/version changed | `winget show --id ... --exact`; verify upstream linked download, do not choose unrelated package |
| Homebrew installed but not in PATH | Shell environment setup omitted | Follow brew's printed instructions; use `brew --prefix`, not hard-coded architecture paths |
| Tesseract reports missing language | Engine installed, trained data unresolved | Pass `--tessdata-dir` to bundled resources and inspect `--list-langs` |
| Chinese OCR smoke fails | Probe/font/data/runtime mismatch | Use bundled licensed font and trained data; inspect actual recognized text and probe hash; never lower accuracy assertions to hide a failure |
| Venv stops after moving repository | Venv contains old absolute paths | Stop tasks; move old venv aside; recreate/install in new location |
| Migration or Skill installation rejects a macOS `/var/...` path | The OS temporary directory can use the `/var` symlink to `/private/var`; source/destination ancestor links are deliberately rejected | Verify the trusted base directory and use its real `/private/var/...` path. Tests canonicalize only their trusted temporary root before creating deliberate links; never silently resolve an untrusted case/input link to bypass the guard |
| ZIP extraction fails under long paths | Nested archive/path/tool limits | Extract to a short local directory; preserve originals; don't flatten source folders |
| Network share executable fails | Share permissions, policy or file locks | Keep runtime/venv local; place cases on a writable share only after a read/write check; no automatic SMB reconfiguration |
| Office export works but opening fails | Shared-path/access/application context or corrupt output | Read back generated file with openpyxl/python-docx; test local copy and hostname-based share separately |

### Evidence and research pitfalls

| Tempting shortcut | Why it is wrong | Required correction |
| --- | --- | --- |
| "The image/logo matches, so it is the factory" | Images are reposted; labels may be unrelated to manufacturing | Compare product details and separately bind legal entity, physical site, process and batch |
| "Platform factory badge proves the mould owner" | Badge may describe a seller or broad capability | Obtain target tooling/process evidence and supplier-site responsibility chain |
| "A certificate belongs to the seller" | Licence holder and manufacturing site can differ | Verify exact SKU, ratings, dates, holder, authorized site and process scope from official records |
| "A social profile filmed machines" | It may show a customer/subcontractor or reused media | Bind account identity, filming location/date, process, product and original upload chain |
| "Five shops show the same picture" | One upstream image is not five independent witnesses | Deduplicate source families and compare first known publication carefully |
| "Search got zero results" | Index/login/language/access limits exist | Record the query/channel/status; use other sources, don't claim absence |
| "A 90-point score means 90% probability" | Rule score is not a calibrated probability model | Report scores/states by axis and identify evidence gaps |
| "Local origin preference raises factory probability" | Procurement preference is not source evidence | Keep purchasing fit separate from attribution |
| "Audit PASS means the actual source is found" | Operational readiness differs from confirmation | Preserve stage label; confirmed needs strict product/site/process/batch gates |
| "LLM says this must be the supplier" | Model output is an inference, not a primary source | Log model provenance, verify claims against original evidence |
| "More workers means faster and better" | RAM/IO/site throttling can worsen reliability | Start bounded, observe bottlenecks, keep per-host delay and retries finite |
| "Just fetch every posted URL" | Unknown targets/redirects can access unintended network services | Review intended public URLs; do not expose fetch as an untrusted public service |

### Recovery without damaging cases

1. Preserve the full stderr and failed command locally; redact them before sharing because they may contain file paths, usernames or confidential URLs.
2. Print the interpreter executable/version and run its `-m pip check`. Distinguish a source bug, dependency conflict, missing optional tool, and incomplete research.
3. Re-run the smallest failing step; do not re-ingest or overwrite case originals merely to fix an environment.
4. For schema failures, read the exact failing field and compare with `schemas`; templates are examples, not validated real claims.
5. For corrupt/locked report files, close the viewer, choose a new output directory, regenerate, and read back. Keep originals untouched.
6. For a real research blockage, record `blocked`, `login_required`, or the appropriate access status; continue independent sources and identify missing evidence.
7. Before publication, review both file contents and Git history. Removing a secret from the current file or adding `.gitignore` is not remediation for a committed secret. See [Security](../SECURITY.md).

### Repeatable acceptance record

Record **OS, Python version, install tier, command, exit code, expected result, actual result, and UTC time** locally. Do not publish actual machine identifiers or customer data. A successful minimal CLI test, full Python test, external-media test, and factory-attribution confirmation are four different claims.

The OCR smoke uses licensed bundled font assets where available, so it should not depend on a private system font. That improves portability but does not eliminate platform/runtime differences; keep an explicit failure if strict simplified/traditional-Chinese recognition does not pass.

---

## 中文

这是 [有序部署](../DEPLOY.md) 的失败处理配套手册，不声称所有平台已实测。每一步都用明确选定的同一 venv 解释器。

### 必须顺序与停止条件

| 顺序 | 操作 | 通过条件 | 停止情形 |
| --- | --- | --- | --- |
| 1 | 确认 Python 真实路径/版本 | 标准 3.11–3.14 | 错版/未知别名/实验 ABI |
| 2 | 克隆/解压并看根目录 | 有 README、toolkit、skills | ZIP 查看器/错层目录 |
| 3 | 新建本地 venv | 解释器指向目标 venv | 搬移/复制旧环境 |
| 4 | Core 安装、pip check、CLI | 无破依赖、命令正常 | 构建/下载/导入错 |
| 5 | 仓库外案件/检查目录 | 输出不进源码树 | 生产数据会进 Git |
| 6 | 按需 full Python | Office/OpenCV/YAML 导入正常 | 可选包缺或 wheel 冲突 |
| 7 | 按需系统工具探测 | 四工具版本正常 | 程序不能运行 |
| 8 | 语言数据与实际能力测试 | 语言列表/回读正常 | 引擎有但数据/字体/媒体不可用 |
| 9 | 单一目录安装 Skill | 可见且指向正确 toolkit | 重复冲突/错根目录 |
| 10 | 演示案件与报告 | 输出有效、无无证确认 | Schema/模板/路径错 |
| 11 | 单独浏览器/搜索认证 | 目标页与回执可用 | 登录/验证码/连接器限制 |
| 12 | 真调查，公开前审查 | 证据来源链和隐私通过 | 假确定性/重复证据/敏感材料 |

### 环境坑

| 症状 | 原因/检查 | 安全处理 |
| --- | --- | --- |
| `py -3.13` 找不到 | 无启动器/运行时或版本代际不同 | 官方安装支持版、新开终端，或完整解释器路径 |
| `python` 打开商店 | 应用执行别名 | 不盲改全局设置，直接调用已安装程序 |
| 版本断言失败 | 非 3.11–3.14 | 建 venv 前选对版，不改系统软链接 |
| Linux 无 ensurepip/venv | 发行版拆包 | 装同版本 `pythonX.Y-venv` 后用同解释器重试 |
| externally-managed | 往系统 Python 装包 | 用 venv，不用 `--break-system-packages` |
| Activate.ps1 拒绝 | 执行策略 | 直接 venv python，无需改全局策略 |
| 第三方校验脚本出现 `UnicodeDecodeError: gbk` | 未指定 UTF-8 就读取双语文件 | 仅本次命令使用 `python -X utf8` 或进程变量 `PYTHONUTF8=1`，不改机器区域设置 |
| No module factorytrace | 错解释器/未安装 | 打印 sys.executable，用其 -m pip 安装 toolkit |
| 找不到 factorytrace | 未激活/PATH | venv python 加 `-m factorytrace` |
| pip 找不到锁定版本/wheel | 快照/镜像/Python/架构不匹配 | 读完整错误，按元数据范围装、记版本，不关 TLS |
| 要求编译器 | 所选 ABI/架构无 wheel | 标准支持版；必要时官方构建前置，不假定都有 wheel |
| docx/cv2 导入失败 | 未装 extras/导入名不同 | 装 reports/media/full；python-docx 导入 docx，OpenCV 导入 cv2 |
| Unix full 表现异常 | `[full]` 未引用发生 glob | 整个安装目标加引号 |
| FFmpeg 有但视频错 | 无 ffprobe/编解码器坏 | 两个程序都测，再用能力测试定位 |
| Windows 装完找不到 | 当前 PATH 陈旧/其他安装位置 | 新开终端，Get-Command，不装冲突重复套 |
| Winget ID 消失 | 目录变动 | show exact 核验或上游链接，不选无关包 |
| Homebrew 不在 PATH | shell 初始化未做 | 按安装输出配置，用 brew --prefix |
| Tesseract 缺语言 | 引擎与数据分离 | 明确 tessdata-dir 与 list-langs |
| 中文 OCR 测试失败 | 探针/字体/数据/运行时 | 用授权包内字体/数据，查实际文字/哈希，不降低准确断言掩盖 |
| 搬仓库后 venv 坏 | 路径固化 | 停任务、旧 venv 移开、新建重装 |
| macOS 的 `/var/...` 迁移或 Skill 安装被拒绝 | 系统临时目录可能通过 `/var` 链接指向 `/private/var`；源/目标的祖先链接会被有意拒绝 | 核实可信根目录后使用真实 `/private/var/...` 路径。测试只先规范化可信临时根，再创建故意拒绝的链接；不要自动解析不可信案件/输入链接来绕过保护 |
| ZIP 长路径错 | 多层目录/工具限制 | 短本地目录解压，不压平源码，不改原件 |
| 共享盘运行程序错 | 权限/策略/锁 | runtime/venv 本地，案件共享先读写验，不自动改 SMB |
| Office 生成但打不开 | 路径权限/应用上下文/损坏 | openpyxl/docx 回读，测试本地副本与主机名共享 |

### 证据与研究坑

| 错误捷径 | 原因 | 纠正 |
| --- | --- | --- |
| 同图/商标一致就是厂 | 转载/商标与生产可无关 | 产品细节与主体/地点/工序/批次分别绑定 |
| 平台工厂标就是模具厂 | 广义资质非该模具 | 目标模具/工序证据与责任链 |
| 持证人就是制造地点 | 可完全不同 | 官方精确 SKU/参数/日期/主体/获准地点/范围 |
| 社媒拍机器就是自产 | 客户/外协/转载可能 | 账号身份、拍摄地点日期、工序、产品、首发来源链 |
| 五店同图五份独立证据 | 单一上游图 | 来源族去重，首发时间谨慎比对 |
| 搜索零结果就是没有 | 索引/登录/语言/访问限制 | 记查询通道状态，换源，不写不存在 |
| 90 分就是 90% | 规则分非校准概率 | 分轴评分/状态，指出缺口 |
| 采购偏好抬高源头置信 | 偏好不是证据 | 采购适配与归属分开 |
| operational PASS 找到源头 | 流程与归属不同 | 保留阶段，confirmed 严格产品/地点/工序/批次 |
| 模型说一定是谁 | 推断非原始证据 | 记模型来源，对原件核验 |
| 并发越高越好 | 内存/IO/限流损可靠性 | 有界起步、看瓶颈、每站延时有限重试 |
| URL 全部直接抓 | 未知目标/跳转有网络风险 | 只审过公网 URL，不暴露公共 fetch 服务 |

### 保案件的恢复

1. 本地保留完整 stderr 和命令，对外前脱敏用户名、路径、保密网址。
2. 看真实解释器/版本和 pip check，分清源码 bug、依赖冲突、缺可选工具、研究未完成。
3. 只重跑最小失败步，不为修环境覆盖原件或重复入库。
4. Schema 失败看具体字段，对照 schemas；模板只是示例，不是真实主张。
5. 报告锁/损坏先关查看器、新输出目录重生回读，保原件。
6. 阻断记 blocked/login_required 等真实状态，继续独立源，列缺证据。
7. 发布前看内容和 Git 历史；删当前密钥/加 gitignore 不等于历史泄露已修复，见 [安全](../SECURITY.md)。

### 可重复验收记录

本地记录**系统、Python、安装层级、命令、退出码、预期、实际、UTC 时间**，不公开机器真实标识或客户数据。最小 CLI、全 Python、媒体实测、厂家归属确认是四个不同结论。

OCR 测试尽可能用包内授权字体，不依赖私有系统字体；仍不能消除平台差异，严格简繁识别未过要保留失败。
