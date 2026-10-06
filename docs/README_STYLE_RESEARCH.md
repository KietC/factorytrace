# README Design Research and Applied Decisions

[English](#english) · [中文](#中文) · [Project](../README.md)

## English

Research snapshot: **2026-10-05**. Public repository/readme pages were inspected; the star counts below are date-specific GitHub API observations, not permanent metadata. Stars were used to select widely read examples—not as a guarantee of quality, security, suitability, or correctness. This document paraphrases structural lessons; it does not copy their README prose or code.

### Primary examples

| Project | Stars at snapshot | Useful structural pattern | Applied here |
| --- | ---: | --- | --- |
| [Best-README-Template](https://github.com/othneildrew/Best-README-Template) | 16,388 | Purpose, contents, prerequisites, installation, usage, contribution, licence | Short entry point with navigable sections and separate deployment guide |
| [Ruff](https://github.com/astral-sh/ruff) | 49,921 | Clear claim, directly usable installation/usage, deeper docs links, support/licence | Minimal runnable core path; explicit boundaries; link detailed configuration rather than bury it |
| [FastAPI](https://github.com/fastapi/fastapi) | 102,828 | Documentation/source entry points, small example, expected behavior, expansion path | First-case commands and expected outputs; optional full path; separate contribution/security files |

The counts are nonessential selection context. Recheck the repositories if exact contemporary counts matter. A polished README does not establish test coverage or safety; tests, licence scope, dependency metadata, and limitations must be checked independently.

### Official guidance consulted

- [GitHub: About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes): project purpose, getting started, help, and relative links.
- [GitHub: Markdown syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax): headings, links, lists, and fenced examples.
- [Python: venv](https://docs.python.org/3/library/venv.html): isolated environments and interpreter-specific paths; recreate instead of transferring environments.
- [Python: Windows](https://docs.python.org/3/using/windows.html): current install-manager/launcher behavior, with legacy behavior distinguished.
- [Homebrew Python formula](https://formulae.brew.sh/formula/python@3.13): version-specific installation and prefix discovery.
- [Tesseract installation](https://tesseract-ocr.github.io/tessdoc/Installation.html): OCR engine and language data are separate.
- [FFmpeg downloads](https://ffmpeg.org/download.html): upstream source and linked platform builds; do not label every binary distributor as the upstream project.
- [Homebrew ExifTool formula](https://formulae.brew.sh/formula/exiftool): macOS package-managed path.
- [Official Skill guidance](https://learn.chatgpt.com/docs/customization/overview#skills): user/project skill locations; old application paths require actual version checks.

### Applied Markdown conventions

1. **English first, Chinese after:** one complete English section and then one complete Chinese section. Avoid alternating languages every sentence; commands are repeated where needed for standalone reading.
2. **One clear title:** factual scope, not claims such as "guaranteed factory probability" or "all platforms verified".
3. **Small truthful badges:** licence and declared Python range only; no passing-CI badge until a real public run supports it.
4. **Short README, detailed runbook:** installation order, failure checkpoints, and recovery live in `DEPLOY.md`; pitfall tables live in the setup companion.
5. **Commands match source:** actual CLI flags, toolkit subdirectory, extras, wrapper root, and explicit Skill target; no imaginary installer or model requirement.
6. **Fenced language-labelled commands:** `powershell`, `bash`, `text`; variables and paths quoted; explanatory text separated from runnable code.
7. **Relative local links:** portable within clone/archive; external sources use descriptive HTTPS links. No machine-specific file URLs or local private paths.
8. **Expected output and limitation:** every major deployment checkpoint describes success and failure; operational PASS is separate from factory confirmation.
9. **No publishing real cases:** documentation examples are blank/synthetic, accounts/contacts/secrets are excluded, and production data remains outside Git.
10. **Contribution/security/licence separations:** maintainers can accept sanitized reproductions without inviting real business evidence or vulnerable payloads into public issues.

### Pre-publication review

Check Markdown link targets, fence balance, English-before-Chinese order, supported interpreter range, executable argument names, case paths outside source, package/system-tool separation, truthful validation language, no real business identifiers, and third-party licence notices. Re-run this review when installation commands, Skill locations, package metadata, or source layouts change.

This is a living design record, not a certification. Prefer a smaller accurate guide over adding impressive but untested automation.

---

## 中文

研究快照：**2026-10-05**。已看公开仓库/README；星数为当日 GitHub API 观察，不是永久信息。高星只用于挑选广泛阅读的格式样本，不保证质量、安全、适配或正确。这里只归纳结构，不复制正文和代码。

### 主要样本

| 项目 | 当日 stars | 结构启发 | 本项目应用 |
| --- | ---: | --- | --- |
| [Best-README-Template](https://github.com/othneildrew/Best-README-Template) | 16,388 | 用途、目录、前置、安装、用法、贡献、许可 | 易导航入口 + 单独详细部署 |
| [Ruff](https://github.com/astral-sh/ruff) | 49,921 | 明确主张、能运行安装/用法、深入文档、支持/许可 | 最小 core 路径、清楚边界、详配另链 |
| [FastAPI](https://github.com/fastapi/fastapi) | 102,828 | 文档/源码入口、小例子、预期行为、扩展路径 | 首案命令/预期、可选 full、贡献/安全分开 |

星数只是选样背景，精确当前值要重查。README 漂亮不证明覆盖率或安全，测试、许可、依赖与限制必须另核。

### 查过的官方资料

- [GitHub README 指南](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)：目的、起步、支持和相对链接。
- [GitHub Markdown](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)：标题、链接、列表和代码围栏。
- [Python venv](https://docs.python.org/3/library/venv.html)：隔离环境与路径；重建不迁移环境。
- [Python Windows](https://docs.python.org/3/using/windows.html)：当前安装管理器/启动器并区分旧版。
- [Homebrew Python](https://formulae.brew.sh/formula/python@3.13)：指定版本与 prefix。
- [Tesseract 安装](https://tesseract-ocr.github.io/tessdoc/Installation.html)：引擎与语言数据分开。
- [FFmpeg 下载](https://ffmpeg.org/download.html)：上游源码与第三方构建链接，不把所有分发者说成上游。
- [ExifTool Homebrew](https://formulae.brew.sh/formula/exiftool)：macOS 包管理。
- [官方 Skill](https://learn.chatgpt.com/docs/customization/overview#skills)：用户/项目目录；旧应用路径核对版本。

### 已采用格式

1. **英前中后：** 完整英文区再完整中文区，不逐句交替；必要命令两区都给。
2. **一个明确标题：** 不写“保证概率”“全平台已验证”之类不实主张。
3. **少而真的徽章：** 仅许可证和声明 Python 范围，无实测公开 CI 不挂绿标。
4. **入口与详手册分开：** README 快速入口，DEPLOY 配置顺序/恢复，踩坑表另文件。
5. **命令对应源码：** 真参数/目录/extras/包装器/Skill 目标，不虚构自动安装或模型要求。
6. **代码围栏注明语言：** powershell/bash/text，变量路径引号，说明不混进可执行段。
7. **本地相对链接：** 克隆/压缩包可移植，外链描述性 HTTPS，不放私有路径。
8. **预期与限制：** 部署每阶段给结果，operational 不冒充厂家确认。
9. **不公开案件：** 空白/合成例子，排账号/联系人/密钥，生产数据在 Git 外。
10. **贡献/安全/许可独立：** 接受脱敏复现，不鼓励公开业务证据/攻击输入。

### 发布前复核

查链接、围栏、英前中后、Python 范围、参数、仓库外案件、Python/系统工具分离、真实验收说法、无业务标识、第三方许可；安装命令/Skill 目录/元数据/结构变化后重做。

这是迭代设计记录，不是认证。宁可小而准，不加未经验证的炫技自动化。
