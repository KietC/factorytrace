# Troubleshooting

## English

Diagnose from the selected interpreter and the first complete error. If factorytrace is missing, inspect the project venv or use python -m factorytrace; do not assume PATH refreshed. Recreate moved/foreign venvs rather than patching embedded paths. Missing python-docx/openpyxl/OpenCV/PyYAML means the corresponding full extra is not installed. Media-package installation is not proof of executability; run real ffmpeg/ffprobe, Tesseract and ExifTool probes. Unicode paths require UTF-8 end to end. OCR language listing is not enough: use the fixed language data and strict synthetic probes. Audit failures may correctly signal missing material, broken references, bad hashes or unsupported attribution. Never rehash altered evidence merely to force a pass. The root setup/pitfalls guide gives step-by-step recovery commands.

For ordered cross-platform commands, expected outputs and recovery actions, use [DEPLOY.md](../DEPLOY.md). The Chinese reference below retains the full method details; command names and schemas are language-independent.

## 中文详细参考

# 故障排查

## `ModuleNotFoundError: PIL`

没有安装依赖：

```bash
python -m pip install --constraint constraints-tested.txt -e .
```

## PowerShell中文乱码

PowerShell 5.1 默认编码可能错误：

```powershell
Get-Content .\file.md -Encoding UTF8
$env:PYTHONUTF8 = "1"
```

## 中文路径变成 `???`

- 使用 Python `Path` 和当前目录相对路径；
- 不要把 PowerShell 枚举结果交给 `cmd /c`；
- 为不支持Unicode的老工具复制到英文短临时目录，保留原件哈希和映射。

## `audit research` 失败

查看 `errors`：

- 缺目录/模板：重新 `factorytrace init ... --resume`；
- 原件未登记：使用 `factorytrace ingest`；
- 哈希不符：不要重算并覆盖证据，先调查文件为何变化；
- candidate JSON错误：从模板重新复制，保留旧文件为历史。
- 从1.x升级的旧案件先执行`factorytrace migrate --case-root OLD --to 2`；命令创建独立副本、保留源文件和哈希，不允许原地覆盖。随后在副本执行`factorytrace validate`、`assess`、`ledger`和`audit`。

## `audit operational`提示模型模式未声明

这不是要求安装模型，而是要求如实记录：

```bash
factorytrace doctor --case-root CASE --model-mode none
```

如果由Codex/API协助，使用`cloud --model-id <实际ID或unknown-not-preserved>`并填写`logs/model_usage_log.csv`。Lens/Bing等用`--external-visual-service`单独记录。

## `audit confirmed` 一直失败

这是正常阻断。常见缺口：

- 没有准确制造地点；
- 只有同类设备，没有目标工序现场证据；
- 没有精确 SKU/批次；
- 合同、收款、制造主体关系未解释；
- 强证据未保存本地原件/哈希；
- 少于两个独立直接证据簇。
- `materials_confirmed.json`未PASS；
- claim/evidence/ledger引用不完整；
- 环境、模型或执行日志缺失；
- confirmed证据缺少时间、观察事实、限制或review状态。

不要通过手改 CSV 或 verdict 绕过。

## 抓取显示 `robots-denied`

该 URL 未自动抓取。使用正常浏览器打开公开页面，手动保存页面/PDF/截图，再执行 `ingest`。不要为了抓取证据绕过验证码、登录或访问控制。

## HTTP 429/503

```bash
factorytrace fetch urls.csv --case-root CASE \
  --workers 8 --per-host 1 --delay 3 --retries 5
```

工具尊重 `Retry-After`。持续失败时停止自动请求，改为浏览器或稍后复查。

## 页面被重定向到登录页

自动下载保存的只是登录页，不能当产品规格证据。使用已登录浏览器正常访问，保存截图、HTML/PDF和最终URL；证据备注写明登录态和可见范围。

## 图片相似度很高

`triage_similarity` 只是筛选：

- 同一营销图缩放/压缩会很高；
- 同一模具不同角度会很低；
- 透视、光照、背景和裁剪会扭曲结果。

同模判断必须使用统一拍摄、尺度标定、不可调几何和必要的3D/表面测量。

## 旧案件 checksum mismatch

不要直接重算 checksum 让旧 `complete` 通过。先检查变更原因、旧结论是否被后续事实推翻、候选结构化证据是否仍成立。历史报告可以保留，但当前状态必须另行标记 superseded。
