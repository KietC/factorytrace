# Deployment, Configuration Order, and First Case

[English](#english) · [中文](#中文) · [Project](README.md) · [Pitfalls](docs/SETUP_AND_PITFALLS.md)

## English

Follow this sequence on a fresh machine. Run one checkpoint at a time; do not continue after an unexplained error. Commands assume the repository root unless stated otherwise. Example paths are generic, not a production deployment.

### 1. Choose a tier

**Core** handles case/evidence operations without external media engines. **Full Python** adds Office reporting, OpenCV, and YAML but does not install system tools. **Full media** adds FFmpeg/ffprobe, Tesseract, and ExifTool. The **Agent Skill** is optional; the CLI works without Codex or a language model. Assisted research separately needs an application, model/account, browser/search tools, and platform login.

Examples select Python 3.13; metadata allows 3.11–3.14. Prefer a standard supported interpreter, not an experimental/free-threaded build. Never copy `.venv` between computers or operating systems: it contains machine-specific paths. [Python venv documentation](https://docs.python.org/3/library/venv.html).

### 2. Prerequisites and source

#### Windows PowerShell

Install [Git](https://git-scm.com/downloads) and [supported Python](https://www.python.org/downloads/windows/). The current Python Install Manager can install a selected runtime with `py install 3.13`; older launchers may lack this command, so use an official installer instead. Open a new PowerShell:

```powershell
git --version
py -3.13 --version
git clone https://github.com/KietC/factorytrace.git
Set-Location -LiteralPath .\factorytrace
$RepositoryPath = (Get-Location).Path
$ToolkitPath = Join-Path $RepositoryPath 'factory_trace_toolkit'
py -3.13 -c "import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version; print(sys.executable)"
```

Expected: Git version, `Python 3.13.x`, selected interpreter path. If `py` is absent, use the actual installed `python.exe` full path for both checking and creating the environment below. Do not trust an unverified Windows Store alias or unknown global `python`.

#### macOS

Install Homebrew using its [official instructions](https://brew.sh/) if using this route:

```bash
brew install git python@3.13
git --version
PYTHON_BIN="$(brew --prefix python@3.13)/bin/python3.13"
"$PYTHON_BIN" --version
git clone https://github.com/KietC/factorytrace.git
cd factorytrace
REPOSITORY_PATH="$PWD"
TOOLKIT_PATH="$REPOSITORY_PATH/factory_trace_toolkit"
"$PYTHON_BIN" -c 'import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version; print(sys.executable)'
```

Expected: 3.13.x. `brew --prefix` avoids assuming Intel/Apple Silicon installation paths. An official python.org installer is also valid; set `PYTHON_BIN` to its actual interpreter. [Homebrew Python formula](https://formulae.brew.sh/formula/python@3.13).

#### Linux

Debian/Ubuntu-style example:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip
git --version
python3 --version
PYTHON_BIN=python3
"$PYTHON_BIN" -c 'import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version; print(sys.executable)'
git clone https://github.com/KietC/factorytrace.git
cd factorytrace
REPOSITORY_PATH="$PWD"
TOOLKIT_PATH="$REPOSITORY_PATH/factory_trace_toolkit"
```

Expected: Python 3.11–3.14. If the distribution only supplies an older version, stop and install a supported interpreter by that distribution's documented method, then set `PYTHON_BIN`. Do not replace `/usr/bin/python3` or alter its symlinks. Other distributions need their own package manager; apt is not universal.

If using a ZIP download, extract it first and open a terminal in the directory containing this document, not an archive viewer. Git is optional until updating/contributing.

### 3. New environment and core

Windows:

```powershell
py -3.13 -m venv (Join-Path $ToolkitPath '.venv')
$ToolkitPython = Join-Path $ToolkitPath '.venv\Scripts\python.exe'
& $ToolkitPython -c "import sys; print(sys.version); print(sys.executable)"
& $ToolkitPython -m pip install --upgrade pip
& $ToolkitPython -m pip install -e $ToolkitPath
& $ToolkitPython -m pip check
& $ToolkitPython -m factorytrace --version
& $ToolkitPython -m factorytrace --help
```

macOS / Linux:

```bash
"$PYTHON_BIN" -m venv "$TOOLKIT_PATH/.venv"
TOOLKIT_PYTHON="$TOOLKIT_PATH/.venv/bin/python"
"$TOOLKIT_PYTHON" -c 'import sys; print(sys.version); print(sys.executable)'
"$TOOLKIT_PYTHON" -m pip install --upgrade pip
"$TOOLKIT_PYTHON" -m pip install -e "$TOOLKIT_PATH"
"$TOOLKIT_PYTHON" -m pip check
"$TOOLKIT_PYTHON" -m factorytrace --version
"$TOOLKIT_PYTHON" -m factorytrace --help
```

Expected: interpreter path inside this `.venv`; `No broken requirements found`; version `2.0.0`; CLI help. Explicit interpreter paths avoid activation-script policies and PATH conflicts.

These commands use package metadata's dependency ranges. `constraints-tested.txt` is a historical exact test snapshot, not a universal future lockfile. To try it, add `--constraint "$ToolkitPath\constraints-tested.txt"` on Windows or `--constraint "$TOOLKIT_PATH/constraints-tested.txt"` on Unix to the install command. On version/wheel conflicts, follow [pitfalls](docs/SETUP_AND_PITFALLS.md) and record changes; never disable TLS to solve package problems.

`bootstrap.ps1`/`bootstrap.sh` are optional conveniences. Windows bootstrap chooses `py -3`, potentially selecting an unsupported newer interpreter; the sequence above deliberately selects an exact one. Full bootstrap also installs system tools: inspect it before use on shared machines.

### 4. External case and receipt directories

Windows:

```powershell
$CasesPath = Join-Path $env:USERPROFILE 'FactoryTraceCases'
$ChecksPath = Join-Path $CasesPath '_checks'
New-Item -ItemType Directory -Path $ChecksPath -Force | Out-Null
& $ToolkitPython -m factorytrace doctor --model-mode none --output (Join-Path $ChecksPath 'environment.json')
```

macOS / Linux:

```bash
CASES_PATH="$HOME/FactoryTraceCases"
CHECKS_PATH="$CASES_PATH/_checks"
mkdir -p "$CHECKS_PATH"
"$TOOLKIT_PYTHON" -m factorytrace doctor --model-mode none --output "$CHECKS_PATH/environment.json"
```

Expected: local JSON outside the repository. It may contain local paths/system characteristics; do not commit it. Missing optional media tools are acceptable for core, not full-media acceptance. `--model-mode none` declares this run only; it does not infer other conversations' model history.

### 5. Full Python, then separate system tools

Skip if core is enough.

#### 5.1 Full Python

Windows:

```powershell
& $ToolkitPython -m pip install -e "${ToolkitPath}[full]"
& $ToolkitPython -m pip check
& $ToolkitPython -c "import PIL, jsonschema, openpyxl, docx, cv2, yaml; print('Full Python imports: OK')"
```

macOS / Linux:

```bash
"$TOOLKIT_PYTHON" -m pip install -e "$TOOLKIT_PATH[full]"
"$TOOLKIT_PYTHON" -m pip check
"$TOOLKIT_PYTHON" -c "import PIL, jsonschema, openpyxl, docx, cv2, yaml; print('Full Python imports: OK')"
```

Expected: full imports `OK`. Quote `[full]` on Unix to avoid glob expansion.

#### 5.2 System media tools

Windows: inspect exact identities before installing. IDs can change; never accept an unrelated result.

```powershell
winget show --id Gyan.FFmpeg --exact
winget show --id tesseract-ocr.tesseract --exact
winget show --id OliverBetz.ExifTool --exact
winget install --id Gyan.FFmpeg --exact
winget install --id tesseract-ocr.tesseract --exact
winget install --id OliverBetz.ExifTool --exact
```

If unavailable, use trusted downloads linked by upstream [FFmpeg](https://ffmpeg.org/download.html), [Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html), and [ExifTool](https://exiftool.org/). Tesseract may require elevation. Do not install conflicting distributions to hide a failure. Open a new PowerShell and restore steps 2–4's variables before testing.

macOS:

```bash
brew install ffmpeg tesseract exiftool
```

Debian/Ubuntu-style Linux:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg tesseract-ocr libimage-exiftool-perl
```

Other Linux distributions need their documented package names/repositories. The bundled helper supports apt/dnf/pacman routes; availability remains distribution-specific.

#### 5.3 Probes and OCR languages

All platforms:

```text
ffmpeg -version
ffprobe -version
tesseract --version
exiftool -ver
```

Expected: all four show version text. Verify the bundled OCR data explicitly:

Windows:

```powershell
tesseract --tessdata-dir (Join-Path $ToolkitPath 'resources\tessdata') --list-langs
```

macOS / Linux:

```bash
tesseract --tessdata-dir "$TOOLKIT_PATH/resources/tessdata" --list-langs
```

Expected: `eng`, `osd`, `chi_sim`, `chi_tra`. Engine and trained data are separate. OCR smoke probes use bundled licensed Noto font assets rather than requiring a private system font; preserve their OFL licence and provenance. Do not place private OCR samples in the resource directory.

### 6. Optional explicit Skill installation

Current official documentation lists user `~/.agents/skills` and project `.agents/skills`. Confirm the actual target application's version/settings; older versions may use `.codex/skills`. Install into **one** confirmed location, not both. No accounts, cookies, model access, browser profiles, or connectors are transferred. [Official guidance](https://learn.chatgpt.com/docs/customization/overview#skills).

Windows:

```powershell
$SkillTarget = Join-Path $env:USERPROFILE '.agents\skills'
& $ToolkitPython .\scripts\install_skill.py --target-dir $SkillTarget
& $ToolkitPython .\skills\trace-source-factory\scripts\factorytrace_cli.py --toolkit-root $ToolkitPath --check-only --print-command
```

macOS / Linux:

```bash
SKILL_TARGET="$HOME/.agents/skills"
"$TOOLKIT_PYTHON" scripts/install_skill.py --target-dir "$SKILL_TARGET"
"$TOOLKIT_PYTHON" skills/trace-source-factory/scripts/factorytrace_cli.py --toolkit-root "$TOOLKIT_PATH" --check-only --print-command
```

For project-local use, explicitly select `REPOSITORY/.agents/skills`. The installer creates the skill subdirectory: identical existing bytes are a no-op; different existing contents are refused. Back up/move the old skill, inspect differences, and rerun—there is no overwrite switch.

Expected: installed/already-installed confirmation, then wrapper discovery shows the intended toolkit command. Reload/restart the agent if needed and verify `trace-source-factory` is visible. If missing, check the directory before copying again. Skill visibility does not prove browser/search connectivity.

Prefer explicit `--toolkit-root`; `FACTORY_TRACE_TOOLKIT` may be session-only. No global PATH changes are necessary.

### 7. Validation checkpoints

**Core acceptance:** steps 2–4 pass. Do not run full-suite checks under core-only dependencies and misclassify optional missing packages as a core failure.

**Full Python acceptance**, without a media-runtime claim:

Windows:

```powershell
Push-Location -LiteralPath $ToolkitPath
& $ToolkitPython -m unittest discover -s tests -v
Pop-Location
& $ToolkitPython -m unittest discover -s .\skills\trace-source-factory\tests -v
& $ToolkitPython .\factory_trace_toolkit\scripts\verify_toolkit.py --root $ToolkitPath --skip-runtime-smoke --output (Join-Path $ChecksPath 'source-verification.json')
```

macOS / Linux:

```bash
(cd "$TOOLKIT_PATH" && "$TOOLKIT_PYTHON" -m unittest discover -s tests -v)
"$TOOLKIT_PYTHON" -m unittest discover -s skills/trace-source-factory/tests -v
"$TOOLKIT_PYTHON" factory_trace_toolkit/scripts/verify_toolkit.py --root "$TOOLKIT_PATH" --skip-runtime-smoke --output "$CHECKS_PATH/source-verification.json"
```

Expected: tests `OK`, verification `status: PASS`; the skip warning explicitly says runtime tools were not verified. Fix checksum/source problems rather than disabling checks.

**Full media acceptance**, after all tool probes pass:

Windows:

```powershell
& $ToolkitPython .\factory_trace_toolkit\scripts\capability_smoke.py --output (Join-Path $ChecksPath 'capability-smoke.json')
& $ToolkitPython .\factory_trace_toolkit\scripts\verify_toolkit.py --root $ToolkitPath --output (Join-Path $ChecksPath 'full-verification.json')
```

macOS / Linux:

```bash
"$TOOLKIT_PYTHON" factory_trace_toolkit/scripts/capability_smoke.py --output "$CHECKS_PATH/capability-smoke.json"
"$TOOLKIT_PYTHON" factory_trace_toolkit/scripts/verify_toolkit.py --root "$TOOLKIT_PATH" --output "$CHECKS_PATH/full-verification.json"
```

Expected: each JSON `status: PASS`, no unexplained errors. OCR/video/Office round trips are stronger than finding executable paths. Keep local receipts private. A pass on this machine does not verify other OS combinations.

### 8. First case and report

Start with the [photo/material checklist](factory_trace_toolkit/PHOTO_MATERIAL_CHECKLIST.md): front/back/side/bottom, ruler/caliper calibration, hole positions, tooling marks, material spec/test, part number, ratings, certification number/source, batch labels. An uncalibrated photo does not provide exact dimensions.

Windows:

```powershell
& $ToolkitPython -m factorytrace init DEMO-001 --root $CasesPath
$CasePath = Join-Path $CasesPath 'DEMO-001'
& $ToolkitPython -m factorytrace validate --case-root $CasePath
& $ToolkitPython -m factorytrace assess --case-root $CasePath
& $ToolkitPython -m factorytrace report --case-root $CasePath --format md,json,csv
& $ToolkitPython -m factorytrace lint-report --case-root $CasePath
```

macOS / Linux:

```bash
"$TOOLKIT_PYTHON" -m factorytrace init DEMO-001 --root "$CASES_PATH"
CASE_PATH="$CASES_PATH/DEMO-001"
"$TOOLKIT_PYTHON" -m factorytrace validate --case-root "$CASE_PATH"
"$TOOLKIT_PYTHON" -m factorytrace assess --case-root "$CASE_PATH"
"$TOOLKIT_PYTHON" -m factorytrace report --case-root "$CASE_PATH" --format md,json,csv
"$TOOLKIT_PYTHON" -m factorytrace lint-report --case-root "$CASE_PATH"
```

Expected: `case.json`, `manifest.json`, `artifacts`, `work`, `evidence`, `candidates`, `output`. Initial placeholders are **not real research** and no factory is confirmed. An existing name needs inspection, a new name, or deliberate `--resume`; do not delete research to get a clean run.

For a real case, fill `work/product_profile.json`, `candidates/CAND-001.json`, and structured records. Replace every placeholder below with your actual paths and invoke through the venv interpreter with `-m factorytrace`:

```text
factorytrace ingest /actual/path/to/originals --recursive --case-root /actual/path/to/case --workers 4
factorytrace queries --case-root /actual/path/to/case
factorytrace materials --case-root /actual/path/to/case --stage discovery
factorytrace validate --case-root /actual/path/to/case
factorytrace assess --case-root /actual/path/to/case
factorytrace hypotheses --case-root /actual/path/to/case
factorytrace report --case-root /actual/path/to/case --format md,json,csv,xlsx,docx
factorytrace lint-report --case-root /actual/path/to/case
factorytrace audit --case-root /actual/path/to/case --stage operational
```

XLSX/DOCX need reports/full extras. `operational` may correctly fail for incomplete materials/records. Resolve the gap without inventing evidence. `confirmed` is a stricter attribution gate, not a test that must be forced green.

### 9. Search/browser and bounded concurrency

Log in on the target machine and authorize the intended browser interaction. Search/browser tools belong to the agent environment, not the Python wheel. Test one benign page and one saved receipt before expanding research; another machine's login state does not transfer.

Use independent source families; reposted images are not independent evidence. Record capture/publication dates, canonical URL, hash, observed fact, and inference separately.

Start ingestion at 4 workers; compare auto caps at 8. Explicit-URL capture defaults to 8 workers, 2 per host, 1-second delay, bounded retry/timeout/size. Increase only after observing RAM/disk/network and site limits. Bandwidth does not justify hammering a site.

Do not feed unreviewed URLs from strangers/pages into `fetch`: it is a trusted-operator capture tool, not an SSRF-hardened public service. Use intended public HTTP(S) evidence URLs. Use normal browser interactions for login/CAPTCHA, and record blocked as unverified. See [Security](SECURITY.md).

### 10. Updates, recovery, removal

Record the current commit and back up cases separately. Check `git status --short`, preserve edits, then `git pull --ff-only`. Reinstall with the same venv interpreter, retest relevant checkpoints, and compare/back up the old Skill before updating.

On repository move/Python upgrade, recreate a venv at the new location. Stop processes and move the old environment aside first; never recursively delete a computed path without confirming its resolved target. Keeping the old venv temporarily allows rollback.

Removal only concerns known installed Skill and repository/environment paths. Cases remain external and must not be deleted with the application. System media tools may be shared and are not automatically uninstalled.

---

## 中文

新机器逐项按顺序做，检查点通过再继续；不明报错先停。除非另说明，命令从仓库根目录运行。示例路径是通用路径，不是生产部署。

### 1. 选择层级

**Core** 做案件/证据操作，不要求媒体引擎。**Full Python** 加 Office、OpenCV、YAML，不装系统工具。**Full media** 再装 FFmpeg/ffprobe、Tesseract、ExifTool。**Agent Skill** 可选，CLI 不依赖 Codex/大模型；辅助研究另需应用、模型/账号、浏览器/搜索工具、单独平台登录。

示例用 Python 3.13，包允许 3.11–3.14。优先标准支持版，不用实验/自由线程构建。不要跨机器/系统复制 `.venv`，内有原机路径。[官方 venv 说明](https://docs.python.org/3/library/venv.html)。

### 2. 先前置工具，再源码

#### Windows PowerShell

装 [Git](https://git-scm.com/downloads) 和 [受支持 Python](https://www.python.org/downloads/windows/)。当前 Python Install Manager 可用 `py install 3.13`，旧启动器无此命令时用官方安装程序。装完新开 PowerShell：

```powershell
git --version
py -3.13 --version
git clone https://github.com/KietC/factorytrace.git
Set-Location -LiteralPath .\factorytrace
$RepositoryPath = (Get-Location).Path
$ToolkitPath = Join-Path $RepositoryPath 'factory_trace_toolkit'
py -3.13 -c "import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version; print(sys.executable)"
```

预期 Git 版本、3.13.x、解释器路径。没有 `py` 则下面检查/创建环境都用实际 `python.exe` 完整路径，不用商店未知别名或未知全局 Python。

#### macOS

按 [Homebrew 官网](https://brew.sh/) 安装后：

```bash
brew install git python@3.13
git --version
PYTHON_BIN="$(brew --prefix python@3.13)/bin/python3.13"
"$PYTHON_BIN" --version
git clone https://github.com/KietC/factorytrace.git
cd factorytrace
REPOSITORY_PATH="$PWD"
TOOLKIT_PATH="$REPOSITORY_PATH/factory_trace_toolkit"
"$PYTHON_BIN" -c 'import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version; print(sys.executable)'
```

预期 3.13.x；`brew --prefix` 不写死 Intel/Apple Silicon 路径。也可用 python.org 安装程序，将 `PYTHON_BIN` 设为实际解释器。[Python 配方](https://formulae.brew.sh/formula/python@3.13)。

#### Linux

Debian/Ubuntu 类示例：

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip
git --version
python3 --version
PYTHON_BIN=python3
"$PYTHON_BIN" -c 'import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version; print(sys.executable)'
git clone https://github.com/KietC/factorytrace.git
cd factorytrace
REPOSITORY_PATH="$PWD"
TOOLKIT_PATH="$REPOSITORY_PATH/factory_trace_toolkit"
```

预期 3.11–3.14，系统旧版则先停，按发行版官方方法装支持版本并指定 `PYTHON_BIN`。不替换 `/usr/bin/python3` 或软链接。apt 不是所有 Linux 通用命令。

ZIP 先解压，在含本文档的目录打开终端，不在压缩包查看器运行；暂不更新/贡献时 Git 可选。

### 3. 新环境与 core

Windows：

```powershell
py -3.13 -m venv (Join-Path $ToolkitPath '.venv')
$ToolkitPython = Join-Path $ToolkitPath '.venv\Scripts\python.exe'
& $ToolkitPython -c "import sys; print(sys.version); print(sys.executable)"
& $ToolkitPython -m pip install --upgrade pip
& $ToolkitPython -m pip install -e $ToolkitPath
& $ToolkitPython -m pip check
& $ToolkitPython -m factorytrace --version
& $ToolkitPython -m factorytrace --help
```

macOS / Linux：

```bash
"$PYTHON_BIN" -m venv "$TOOLKIT_PATH/.venv"
TOOLKIT_PYTHON="$TOOLKIT_PATH/.venv/bin/python"
"$TOOLKIT_PYTHON" -c 'import sys; print(sys.version); print(sys.executable)'
"$TOOLKIT_PYTHON" -m pip install --upgrade pip
"$TOOLKIT_PYTHON" -m pip install -e "$TOOLKIT_PATH"
"$TOOLKIT_PYTHON" -m pip check
"$TOOLKIT_PYTHON" -m factorytrace --version
"$TOOLKIT_PYTHON" -m factorytrace --help
```

预期解释器在本 `.venv`、`No broken requirements found`、版本 `2.0.0`、CLI 帮助。完整路径避开激活脚本策略和 PATH 冲突。

此处按包范围装依赖。`constraints-tested.txt` 是历史精确快照，不保证未来通用。尝试快照时安装命令 Windows 加 `--constraint "$ToolkitPath\constraints-tested.txt"`，Unix 加 `--constraint "$TOOLKIT_PATH/constraints-tested.txt"`。版本/wheel 失败看 [踩坑](docs/SETUP_AND_PITFALLS.md) 并记录，不关 TLS。

bootstrap 可选，Windows 的 `py -3` 可能选到不支持的新版本；上述手动步骤明确选版。Full bootstrap 会装系统工具，共用机器先读脚本。

### 4. 仓库外案件和回执

Windows：

```powershell
$CasesPath = Join-Path $env:USERPROFILE 'FactoryTraceCases'
$ChecksPath = Join-Path $CasesPath '_checks'
New-Item -ItemType Directory -Path $ChecksPath -Force | Out-Null
& $ToolkitPython -m factorytrace doctor --model-mode none --output (Join-Path $ChecksPath 'environment.json')
```

macOS / Linux：

```bash
CASES_PATH="$HOME/FactoryTraceCases"
CHECKS_PATH="$CASES_PATH/_checks"
mkdir -p "$CHECKS_PATH"
"$TOOLKIT_PYTHON" -m factorytrace doctor --model-mode none --output "$CHECKS_PATH/environment.json"
```

预期仓库外 JSON，可能有路径/系统特征，不提交。Core 可缺媒体工具，Full media 不可。`none` 仅声明本次，不推断其他聊天历史。

### 5. 先 Full Python，再系统工具

仅 core 可跳过。

#### 5.1 Full Python

Windows：

```powershell
& $ToolkitPython -m pip install -e "${ToolkitPath}[full]"
& $ToolkitPython -m pip check
& $ToolkitPython -c "import PIL, jsonschema, openpyxl, docx, cv2, yaml; print('Full Python imports: OK')"
```

macOS / Linux：

```bash
"$TOOLKIT_PYTHON" -m pip install -e "$TOOLKIT_PATH[full]"
"$TOOLKIT_PYTHON" -m pip check
"$TOOLKIT_PYTHON" -c "import PIL, jsonschema, openpyxl, docx, cv2, yaml; print('Full Python imports: OK')"
```

预期 `OK`；Unix 给 `[full]` 加引号防 glob。

#### 5.2 系统媒体工具

Windows 先核对准确包身份再安装，ID 可变化，不选无关结果：

```powershell
winget show --id Gyan.FFmpeg --exact
winget show --id tesseract-ocr.tesseract --exact
winget show --id OliverBetz.ExifTool --exact
winget install --id Gyan.FFmpeg --exact
winget install --id tesseract-ocr.tesseract --exact
winget install --id OliverBetz.ExifTool --exact
```

不可用则走 [FFmpeg](https://ffmpeg.org/download.html)、[Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html)、[ExifTool](https://exiftool.org/) 上游可信下载。Tesseract 可能需提权，不装多套冲突工具掩盖失败。新开 PowerShell，重建步骤 2–4 变量再测。

macOS：

```bash
brew install ffmpeg tesseract exiftool
```

Debian/Ubuntu 类：

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg tesseract-ocr libimage-exiftool-perl
```

其他发行版按官方包名/源处理；脚本支持 apt/dnf/pacman 路径，不等于所有发行版必成功。

#### 5.3 程序与 OCR 语言检查

各系统：

```text
ffmpeg -version
ffprobe -version
tesseract --version
exiftool -ver
```

预期四个版本正常，再检查包内数据：

Windows：

```powershell
tesseract --tessdata-dir (Join-Path $ToolkitPath 'resources\tessdata') --list-langs
```

macOS / Linux：

```bash
tesseract --tessdata-dir "$TOOLKIT_PATH/resources/tessdata" --list-langs
```

预期 `eng`、`osd`、`chi_sim`、`chi_tra`；引擎/语言数据分两项。OCR 探针使用包内授权 Noto 字体，不要求私有系统字体，保留 OFL 与来源；不放私有样本进资源目录。

### 6. 可选且明确的 Skill 安装

当前官方用户目录 `~/.agents/skills`、项目 `.agents/skills`；核对目标版本/设置，旧版可能 `.codex/skills`。只装确认的**一个**目录，账号/Cookie/模型权限/浏览器档案/连接器不迁移。[官方说明](https://learn.chatgpt.com/docs/customization/overview#skills)。

Windows：

```powershell
$SkillTarget = Join-Path $env:USERPROFILE '.agents\skills'
& $ToolkitPython .\scripts\install_skill.py --target-dir $SkillTarget
& $ToolkitPython .\skills\trace-source-factory\scripts\factorytrace_cli.py --toolkit-root $ToolkitPath --check-only --print-command
```

macOS / Linux：

```bash
SKILL_TARGET="$HOME/.agents/skills"
"$TOOLKIT_PYTHON" scripts/install_skill.py --target-dir "$SKILL_TARGET"
"$TOOLKIT_PYTHON" skills/trace-source-factory/scripts/factorytrace_cli.py --toolkit-root "$TOOLKIT_PATH" --check-only --print-command
```

项目级明确选 `仓库/.agents/skills`。同字节已安装不重复操作，不同内容拒绝覆盖；自行备份/移走旧版、看差异后重跑，无强制覆盖开关。

预期安装确认、包装器找到目标 toolkit。必要时重载/重启，确认 `trace-source-factory`；不出现先查目录，不乱复制。Skill 出现不代表浏览器/搜索畅通。优先 `--toolkit-root`，环境变量可仅会话，没必要改全局 PATH。

### 7. 分层验收

**Core：** 步骤 2–4 通过；不要 core 环境跑 full 全套，把缺可选包误当 core 失败。

**Full Python**，不证明媒体运行：

Windows：

```powershell
Push-Location -LiteralPath $ToolkitPath
& $ToolkitPython -m unittest discover -s tests -v
Pop-Location
& $ToolkitPython -m unittest discover -s .\skills\trace-source-factory\tests -v
& $ToolkitPython .\factory_trace_toolkit\scripts\verify_toolkit.py --root $ToolkitPath --skip-runtime-smoke --output (Join-Path $ChecksPath 'source-verification.json')
```

macOS / Linux：

```bash
(cd "$TOOLKIT_PATH" && "$TOOLKIT_PYTHON" -m unittest discover -s tests -v)
"$TOOLKIT_PYTHON" -m unittest discover -s skills/trace-source-factory/tests -v
"$TOOLKIT_PYTHON" factory_trace_toolkit/scripts/verify_toolkit.py --root "$TOOLKIT_PATH" --skip-runtime-smoke --output "$CHECKS_PATH/source-verification.json"
```

预期 `OK`、`status: PASS`；明确保留跳过运行能力警告。清单/源码错误修复，不禁用检查。

**Full media**，所有工具版本探测成功后：

Windows：

```powershell
& $ToolkitPython .\factory_trace_toolkit\scripts\capability_smoke.py --output (Join-Path $ChecksPath 'capability-smoke.json')
& $ToolkitPython .\factory_trace_toolkit\scripts\verify_toolkit.py --root $ToolkitPath --output (Join-Path $ChecksPath 'full-verification.json')
```

macOS / Linux：

```bash
"$TOOLKIT_PYTHON" factory_trace_toolkit/scripts/capability_smoke.py --output "$CHECKS_PATH/capability-smoke.json"
"$TOOLKIT_PYTHON" factory_trace_toolkit/scripts/verify_toolkit.py --root "$TOOLKIT_PATH" --output "$CHECKS_PATH/full-verification.json"
```

预期各 `PASS` 无未解释错误，实际 OCR/视频/Office 回读强于仅找到程序；回执不提交，本机过不代表其他系统过。

### 8. 首案与首份报告

先看 [材料清单](factory_trace_toolkit/PHOTO_MATERIAL_CHECKLIST.md)：正/背/侧/底、尺量标定、孔位、模具痕、材质规格/测试、零件号、额定参数、认证编号/源、批次。未标定图片不能精确量尺寸。

Windows：

```powershell
& $ToolkitPython -m factorytrace init DEMO-001 --root $CasesPath
$CasePath = Join-Path $CasesPath 'DEMO-001'
& $ToolkitPython -m factorytrace validate --case-root $CasePath
& $ToolkitPython -m factorytrace assess --case-root $CasePath
& $ToolkitPython -m factorytrace report --case-root $CasePath --format md,json,csv
& $ToolkitPython -m factorytrace lint-report --case-root $CasePath
```

macOS / Linux：

```bash
"$TOOLKIT_PYTHON" -m factorytrace init DEMO-001 --root "$CASES_PATH"
CASE_PATH="$CASES_PATH/DEMO-001"
"$TOOLKIT_PYTHON" -m factorytrace validate --case-root "$CASE_PATH"
"$TOOLKIT_PYTHON" -m factorytrace assess --case-root "$CASE_PATH"
"$TOOLKIT_PYTHON" -m factorytrace report --case-root "$CASE_PATH" --format md,json,csv
"$TOOLKIT_PYTHON" -m factorytrace lint-report --case-root "$CASE_PATH"
```

预期案件基础文件与目录；占位模板**不是研究结果**，没有确认厂家。同名存在先查，换名或有意 `--resume`，不删研究。

真实案件填 product_profile、候选与结构化记录，下述换自己实际路径并用 venv 解释器加 `-m factorytrace`：

```text
factorytrace ingest /actual/path/to/originals --recursive --case-root /actual/path/to/case --workers 4
factorytrace queries --case-root /actual/path/to/case
factorytrace materials --case-root /actual/path/to/case --stage discovery
factorytrace validate --case-root /actual/path/to/case
factorytrace assess --case-root /actual/path/to/case
factorytrace hypotheses --case-root /actual/path/to/case
factorytrace report --case-root /actual/path/to/case --format md,json,csv,xlsx,docx
factorytrace lint-report --case-root /actual/path/to/case
factorytrace audit --case-root /actual/path/to/case --stage operational
```

XLSX/DOCX 要 reports/full；材料/记录不齐 operational 失败正常，按缺口补，不编造。confirmed 是严格归属门槛，不是硬要跑绿的测试。

### 9. 搜索、浏览器、有界并发

目标机器自行登录并授权交互；工具通道属 Agent 不是 wheel。先验一页普通页面和一份回执，另一台机器登录态不迁移。多来源需独立，同图转载不独立，采集/发布日期、网址、哈希、观察/推断分开。

入库先 4 workers，比图 auto 上限 8，明确 URL 抓取默认 8 总并发、2 每站、1 秒延迟、有界重试/超时/大小；观察资源和站点限制再增，不因宽带大压一个站。

不把陌生人/网页未审查 URL 直接交 fetch，它不是已加固的公共 SSRF 服务；仅明确公网 HTTP(S) 证据 URL。登录/验证码正常浏览器处理，阻断记未核实，见 [安全](SECURITY.md)。

### 10. 更新、恢复、移除

记 commit、另备份案件，先 `git status --short` 保留改动，再 `git pull --ff-only`。同 venv 重装复验，Skill 先备份比较。搬仓库/升级 Python 重新建环境，停进程后旧 venv 移开暂存；未核准解析路径不递归删。只移除已知 Skill/仓库/环境，仓库外案件不随程序删，共用系统工具不自动卸载。
