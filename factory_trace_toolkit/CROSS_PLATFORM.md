# Cross-platform operations

## English

Use a fresh project venv on every OS and explicitly select Python 3.11–3.14. Do not copy environments or reuse machine paths. Follow the root deployment guide for Windows PowerShell and macOS/Linux commands. Quote paths with spaces; use UTF-8; keep cases outside the source tree. Match wheelhouses to OS, architecture and Python. Apple Silicon must not mix arm64 and x86_64 packages; Alpine/musl and less common architectures may require core-only or locally built optional dependencies. Start with conservative local workers; image auto-workers are capped. Public-site concurrency is independent of CPU count and stays limited by per-host semaphores/delay/retry policy. A design or CI matrix is not proof that every platform passed. Target-machine acceptance must test actual Unicode paths, dependency integrity and selected capabilities.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# Windows、macOS、Linux与并发运行

完整依赖、最低配置、锁定安装和离线wheelhouse见
[ENVIRONMENT_AND_DEPENDENCIES.md](ENVIRONMENT_AND_DEPENDENCIES.md)。

## 一、统一运行时

- Python 3.11–3.14；`pyproject.toml` 对尚未验收的未来小版本采用上限封闭。
- 核心依赖为 Pillow + jsonschema；默认 full 安装另含 OpenCV、Word/Excel和YAML扩展。
- 核心不需要本地模型、GPU、CUDA或API Key。
- 核心网络层使用 Python，不依赖 PowerShell `Invoke-WebRequest`、macOS专用工具或 GNU-only 参数。
- 路径使用 `pathlib`，JSON/CSV/Markdown统一 UTF-8。

“面向三平台”表示代码和包装脚本按三平台设计，不等于三平台实机矩阵已经全部通过。发布记录仅保留公开软件依赖版本，不披露宿主系统、硬件或环境配置；每台目标机器先运行：

```bash
factorytrace doctor --output environment.current.json --model-mode none --strict
```

仓库已附带`.github/workflows/ci.yml`，定义Windows/macOS/Linux × Python 3.11–3.14矩阵；只有工作流实际运行并保存artifact后，才可以把对应组合标为“CI验证通过”。本地已真实验证Windows/Python 3.13，不把“已定义矩阵”冒充macOS/Linux实机通过。

## 二、安装

### Windows

```powershell
cd <factory_trace_toolkit所在目录>
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
.\.venv\Scripts\python.exe -m factorytrace --help
```

PowerShell 5.1 读取 UTF-8 文件：

```powershell
Get-Content .\README.md -Encoding UTF8
```

### macOS / Linux

```bash
cd /path/to/factory_trace_toolkit
bash scripts/bootstrap.sh
.venv/bin/python -m factorytrace --help
```

## 三、并发分层

### 网络任务

默认：

```text
workers=8
per_host=2
delay=1 second
retries=2
max response=25 MiB
```

高速宽带不等于可以对单站点开几十并发。正确做法是跨域并发、单域克制：

```bash
factorytrace fetch urls.csv --case-root CASE \
  --workers 8 --per-host 2 --delay 1
```

出现 429 时降低 `per-host`、增加 `delay`。Common Crawl等公开基础设施应更慢；登录、验证码和JS站使用正常浏览器，不绕过。

### CPU图片任务

`compare` 使用 ProcessPool：

```bash
factorytrace compare reference.jpg candidates/*.jpg \
  --output CASE/output/image_compare.csv --workers 0
```

`--workers 0` 使用工具的安全auto策略。笔记本避免满核发热时可显式使用 `--workers 2`或`4`；高核桌面先用auto，再根据基准显式调整。

从1.1.0开始，auto不是无限制交给Python：它取
`min(候选数, 逻辑核-1, 8)`。高核工作站必须显式指定更高值并观察RAM、磁盘和温度。

### 磁盘任务

摄取可并发计算哈希，但 manifest 只在短临界区加锁并 atomic replace。不要同时让多个旧脚本直接改同一个 JSON。

## 四、设备建议

快速档位：

| 档位 | 资源 | ingest / compare / fetch |
|---|---|---|
| 最低 | 4核、8GB RAM、5GB空闲 | 2 / 2 / 4，单域1，延迟2秒 |
| 常规 | 8核、16GB RAM、SSD 20GB+ | 4 / 4 / 8，单域2 |
| 工作站 | 16核、32GB RAM、SSD 50GB+ | 8 / 8 / 8，单域2 |

公网单域并发不随本机CPU增加。1688/Alibaba登录态和图片搜索走人工浏览器，不能把高带宽解释为批量抓取许可。

### MacBook

- 使用外接电源；
- 长时间图片比较限制为 50%–75% 逻辑核；
- 案件放在本地 APFS，完成后再同步云盘；
- 云盘同步期间不要移动正在摄取的原件。

### Windows工作站

- PowerShell 5.1 显式 UTF-8；
- 避免把路径写死到任何宿主工作区；
- 长路径和中文路径已支持，但第三方旧工具可在英文短路径副本运行；
- 杀毒软件可能拖慢数千小图哈希，优先使用案件独立目录，不建议全盘排除。

### Linux

- 容器运行时把案件目录只挂载一次；
- 保持宿主和容器 UID/GID 可写；
- 不要用 root 生成后续普通用户无法修改的证据文件。

## 五、可移植打包

打包前：

```bash
factorytrace audit --case-root CASE --stage research
```

Windows：

```powershell
Compress-Archive -LiteralPath .\CASE -DestinationPath .\CASE-portable.zip
Get-FileHash .\CASE-portable.zip -Algorithm SHA256
```

macOS/Linux：

```bash
tar -czf CASE-portable.tar.gz CASE
shasum -a 256 CASE-portable.tar.gz   # macOS
sha256sum CASE-portable.tar.gz       # Linux
```

案件中不保存平台密码、Cookie、OAuth token或私人银行完整账号。登录态浏览器只导出必要的页面、截图或HAR并脱敏。

`package_toolkit.py`生成的是源码便携包，不包含`.venv`、任何OS专用wheel或FFmpeg/Tesseract/ExifTool引擎；默认也排除本机`verification.json`、`environment.current.json`、本地总校验表和含来源绝对路径的`SOURCES_AND_PROVENANCE.md`。ZIP内部重新生成只覆盖实际入包文件的`PACKAGE_CHECKSUMS_SHA256.txt`。如需离线迁移，应按每个OS/架构/Python版本分别制作wheelhouse，并缓存对应系统工具安装包。OpenCV 4.14没有Windows ARM64或musllinux/Alpine预编译wheel，这些组合默认只承诺core-only或自建依赖后重验。

## 六、性能不应破坏证据

- 不使用会覆盖原图的批量压缩。
- 不让并发任务共享无锁 manifest。
- 网络下载先写临时文件，再 atomic rename。
- 下载相同 URL 默认使用缓存；需要刷新时显式 `--force`。
- 同一文件多次出现允许多个路径记录，但按内容哈希聚类，避免丢失来源链。
