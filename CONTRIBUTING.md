# Contributing to FactoryTrace

[English](#english) · [中文](#中文)

## English

Thank you for contributing reproducible, evidence-first improvements. Use [Issues](https://github.com/KietC/factorytrace/issues) for non-sensitive bugs and [Security](SECURITY.md) for vulnerabilities or data disclosure.

### 1. Prepare a clean development environment

Fork/clone the source; follow [DEPLOY.md](DEPLOY.md) using a supported Python and a new venv. Install full extras for the complete test suite. Do not copy another machine's venv or introduce actual research cases, contact data, production screenshots, account sessions, or secrets into your fork.

### 2. Make a focused change

- Keep entity/site/SKU/process/batch separation and uncertainty semantics intact.
- Treat model output, storefront badges, reposted media, and access receipts as leads/metadata—not independently sufficient attribution evidence.
- Add regression tests for bugs and synthetic fixtures for new records. Use reserved example domains and invented labels; do not modify a real case and call it synthetic.
- Write new comments/docstrings in English followed by Chinese when explanatory comments are needed. Avoid noisy restatement of obvious code.
- For public-facing Markdown, provide a complete English section first, then a complete Chinese section. Keep headings, fences, links, and command arguments correct.
- Preserve source provenance and third-party notices. A dependency's licence is not automatically MIT because this project is MIT.

### 3. Run relevant checks

Use your venv interpreter; examples from the repository root on Unix:

```bash
TOOLKIT_PYTHON="$PWD/factory_trace_toolkit/.venv/bin/python"
"$TOOLKIT_PYTHON" -m pip check
(cd factory_trace_toolkit && "$TOOLKIT_PYTHON" -m unittest discover -s tests -v)
"$TOOLKIT_PYTHON" -m unittest discover -s skills/trace-source-factory/tests -v
"$TOOLKIT_PYTHON" factory_trace_toolkit/scripts/verify_toolkit.py --root factory_trace_toolkit --skip-runtime-smoke
```

Windows equivalents use `.\factory_trace_toolkit\.venv\Scripts\python.exe`, PowerShell's `&`, and `Push-Location`/`Pop-Location`; see [deployment validation](DEPLOY.md#7-validation-checkpoints). Full runtime changes additionally need external probes and capability smoke. Checksum manifests must be regenerated after intentional source changes before release verification; do not suppress checksum failures.

State exactly what you ran and on which OS/Python. A skipped runtime check is not a media PASS; a matrix configuration is not cross-platform validation. Synthetic report generation is not manufacturer confirmation.

### 4. Review before opening a pull request

```text
git status --short
git diff --check
git diff --stat
git diff
```

Review each intended file and stage explicitly; do not blindly add the entire working tree. Ensure no case outputs, `.venv`, receipts, access tokens, real contacts, or customer/company-specific details are staged. `.gitignore` does not remove tracked files or historical secrets. Recheck [public release audit](docs/PUBLIC_RELEASE_AUDIT.md).

A useful PR describes the problem, implementation, evidence semantics affected, tests run, platform limitations, and any dependency/resource changes. Include a small synthetic reproduction instead of a real client case. Keep unrelated changes separate.

By submitting code/documentation you intend it to be distributed under this project's [MIT licence](LICENSE), except clearly identified third-party assets retaining their existing licences. Submit only material you have the right to contribute.

### 5. Prepare a source release

Use the manifest-driven packager, not a recursive ZIP of your workspace. First review and normalize text to LF; `.gitattributes` requires LF for portable checksums. Run these from the repository root with the same venv interpreter:

```bash
"$TOOLKIT_PYTHON" factory_trace_toolkit/scripts/hash_toolkit.py
"$TOOLKIT_PYTHON" scripts/verify_public_release.py --write-manifest
"$TOOLKIT_PYTHON" scripts/package_public_release.py --output ../factorytrace-source.zip
```

The packager refuses existing ZIP outputs, requires a passing review, includes only manifest entries, validates CRC/content hashes, and writes a `.zip.sha256` sidecar. Keep artifacts outside the source tree. Stage only reviewed manifest files; check a fresh clone before publishing. Never upload local doctor/test receipts merely to prove that tests ran.

---

## 中文

欢迎可复现、证据优先的改进。非敏感问题用 [Issues](https://github.com/KietC/factorytrace/issues)，漏洞/数据泄露走 [安全说明](SECURITY.md)。

### 1. 干净开发环境

Fork/clone 后按 [DEPLOY.md](DEPLOY.md) 用支持版 Python 新建 venv，完整测试要装 full extras。不复制别机 venv，不往 fork 放真实案件、联系人、生产截图、登录态、密钥。

### 2. 聚焦改动

- 保留主体/地点/SKU/工序/批次分离与不确定性语义。
- 模型输出、店铺标、转载、访问回执是线索/元数据，不是独立足够归属证据。
- Bug 加回归，记录用合成 fixture、保留示例域名和虚构标签；真实案例改几个字不算合成。
- 必要注释/文档串先英语后中文，不重复显而易见代码。
- 公开 Markdown 完整英区在前、中区在后；标题/围栏/链接/参数正确。
- 保留来源/第三方许可，不因项目 MIT 就把依赖许可改 MIT。

### 3. 相关检查

使用 venv 解释器，Unix 根目录示例：

```bash
TOOLKIT_PYTHON="$PWD/factory_trace_toolkit/.venv/bin/python"
"$TOOLKIT_PYTHON" -m pip check
(cd factory_trace_toolkit && "$TOOLKIT_PYTHON" -m unittest discover -s tests -v)
"$TOOLKIT_PYTHON" -m unittest discover -s skills/trace-source-factory/tests -v
"$TOOLKIT_PYTHON" factory_trace_toolkit/scripts/verify_toolkit.py --root factory_trace_toolkit --skip-runtime-smoke
```

Windows 用 `.\factory_trace_toolkit\.venv\Scripts\python.exe`、`&` 与 Push/Pop-Location，见 [部署验收](DEPLOY.md)。运行能力变化还需媒体探测和能力测试；有意改源码后发布前重生清单，不禁用哈希错误。

明确跑了什么、哪个系统/Python；跳过媒体不叫媒体通过，定义矩阵不叫跨平台通过，合成出报告不叫找到厂家。

### 4. PR 前审查

```text
git status --short
git diff --check
git diff --stat
git diff
```

逐文件查并明确 stage，不盲 add 全树，排案件、venv、回执、token、联系人、公司/客户特征。gitignore 不删已追踪/历史敏感，复查 [公开发布审计](docs/PUBLIC_RELEASE_AUDIT.md)。

PR 说明问题、实现、影响的证据语义、测试、平台限制、依赖/资源变化；合成最小复现不是真客户案例，无关改动分开。提交表示自有材料按 [MIT](LICENSE) 分发，明确第三方仍保留原许可，只贡献有权提供的材料。

### 5. 准备源码发布包

使用清单驱动打包器，不递归压缩整个工作目录。先审查并将文本规范为 LF；`.gitattributes` 要求 LF，避免跨平台哈希变化。在仓库根目录用同一个 venv 解释器执行：

```bash
"$TOOLKIT_PYTHON" factory_trace_toolkit/scripts/hash_toolkit.py
"$TOOLKIT_PYTHON" scripts/verify_public_release.py --write-manifest
"$TOOLKIT_PYTHON" scripts/package_public_release.py --output ../factorytrace-source.zip
```

打包器不覆盖已有 ZIP，要求审查通过，只收录清单文件，验证 CRC 与内容哈希，并生成 `.zip.sha256`。产物放仓库外；只暂存审核文件，发布前以全新克隆复验。不能为了证明测试而上传含主机信息的 doctor/测试回执。
