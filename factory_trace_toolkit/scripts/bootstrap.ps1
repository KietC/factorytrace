# English: Create/reuse a local venv, install pinned or flexible dependencies, then probe capabilities.
# 中文：创建或复用本地虚拟环境，安装锁定或宽松依赖后检测能力；CoreOnly 跳过外部媒体工具，已有环境版本仍须合规。
param(
    [switch]$Flexible,
    [switch]$CoreOnly
)

$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$ToolkitRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ToolkitRoot '.venv'

function Assert-NativeSuccess {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

if (-not (Test-Path -LiteralPath $VenvPath)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $VenvPath
        Assert-NativeSuccess 'Create virtual environment with py'
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $VenvPath
        Assert-NativeSuccess 'Create virtual environment with python'
    }
    else {
        throw 'Python 3.11-3.14 was not found.'
    }
}

$PythonExe = Join-Path $VenvPath 'Scripts\python.exe'
& $PythonExe -c "import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version"
Assert-NativeSuccess 'Check Python version'
& $PythonExe -m pip install --upgrade 'pip==26.1.2' 'setuptools==83.0.0'
Assert-NativeSuccess 'Install tested pip and build backend'
$InstallTarget = if ($CoreOnly) { $ToolkitRoot } else { "${ToolkitRoot}[full]" }
if ($Flexible) {
    & $PythonExe -m pip install -e $InstallTarget
    Assert-NativeSuccess 'Install toolkit'
}
else {
    $ConstraintsPath = Join-Path $ToolkitRoot 'constraints-tested.txt'
    & $PythonExe -m pip install --constraint $ConstraintsPath -e $InstallTarget
    Assert-NativeSuccess 'Install toolkit with tested constraints'
}
& $PythonExe -m factorytrace --help
Assert-NativeSuccess 'Run CLI help'
if (-not $CoreOnly) {
    & (Join-Path $PSScriptRoot 'install_media_tools.ps1')
    Assert-NativeSuccess 'Install and verify FFmpeg, Tesseract and ExifTool'
    & $PythonExe (Join-Path $PSScriptRoot 'capability_smoke.py') `
        --output (Join-Path $ToolkitRoot 'output\dependency_capability_smoke.json')
    Assert-NativeSuccess 'Run full dependency capability smoke'
}

& $PythonExe -m factorytrace doctor --output (Join-Path $ToolkitRoot 'environment.current.json') --model-mode undeclared
Assert-NativeSuccess 'Capture environment'

Write-Host "Ready: $PythonExe"
