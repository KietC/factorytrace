# English: Resolve existing media tools before package-manager installation and executable probes.
# 中文：先寻找已有媒体工具，再按需安装并执行版本探测；可能更新用户 PATH 或触发机器级安装，请勿与只读检查混淆。
param()

$ErrorActionPreference = 'Stop'

function Resolve-Tool {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $fallbacks = @{
        tesseract = 'C:\Program Files\Tesseract-OCR\tesseract.exe'
        exiftool = @(
            "$env:LOCALAPPDATA\Programs\ExifTool\exiftool.exe",
            "$env:ProgramFiles\ExifTool\exiftool.exe"
        )
    }
    $wingetLink = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\$Name.exe"
    if (Test-Path -LiteralPath $wingetLink) { return $wingetLink }
    foreach ($fallback in @($fallbacks[$Name])) {
        if ($fallback -and (Test-Path -LiteralPath $fallback)) { return $fallback }
    }
    return $null
}

$packages = @(
    @{ Tool = 'ffmpeg'; WingetId = 'Gyan.FFmpeg'; ChocolateyId = 'ffmpeg'; Scope = 'user' },
    @{ Tool = 'tesseract'; WingetId = 'tesseract-ocr.tesseract'; ChocolateyId = 'tesseract'; Scope = 'machine' },
    @{ Tool = 'exiftool'; WingetId = 'OliverBetz.ExifTool'; ChocolateyId = 'exiftool'; Scope = 'user' }
)

if (@($packages | Where-Object { -not (Resolve-Tool $_.Tool) }).Count -gt 0) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        foreach ($package in $packages) {
            if (-not (Resolve-Tool $package.Tool)) {
                $wingetArguments = @(
                    'install', '--id', $package.WingetId, '--exact',
                    '--scope', $package.Scope,
                    '--accept-package-agreements', '--accept-source-agreements',
                    '--silent', '--disable-interactivity'
                )
                & winget @wingetArguments
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "winget failed for $($package.WingetId) with exit $LASTEXITCODE; Chocolatey fallback will be tried."
                }
            }
        }
    }

    $env:Path = @(
        [Environment]::GetEnvironmentVariable('Path', 'Machine'),
        [Environment]::GetEnvironmentVariable('Path', 'User')
    ) -join ';'
    if (@($packages | Where-Object { -not (Resolve-Tool $_.Tool) }).Count -gt 0 -and `
        (Get-Command choco -ErrorAction SilentlyContinue)) {
        $missingPackages = @(
            $packages |
                Where-Object { -not (Resolve-Tool $_.Tool) } |
                ForEach-Object { $_.ChocolateyId }
        )
        & choco install @missingPackages --yes --no-progress
        if ($LASTEXITCODE -ne 0) {
            throw "Chocolatey install failed: exit $LASTEXITCODE"
        }
    }
}

$env:Path = @(
    [Environment]::GetEnvironmentVariable('Path', 'Machine'),
    [Environment]::GetEnvironmentVariable('Path', 'User')
) -join ';'

$tesseractDir = 'C:\Program Files\Tesseract-OCR'
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$parts = @($userPath -split ';' | Where-Object { $_ })
if ((Test-Path -LiteralPath $tesseractDir) -and $parts -notcontains $tesseractDir) {
    [Environment]::SetEnvironmentVariable('Path', (($parts + $tesseractDir) -join ';'), 'User')
}

$missing = @($packages | Where-Object { -not (Resolve-Tool $_.Tool) } | ForEach-Object { $_.Tool })
if ($missing.Count -gt 0) {
    throw "Installed package verification failed: $($missing -join ', '). Install winget or Chocolatey, then rerun."
}

$versionArguments = @{
    ffmpeg = @('-version')
    tesseract = @('--version')
    exiftool = @('-ver')
}
foreach ($package in $packages) {
    $executable = Resolve-Tool $package.Tool
    $versionOutput = & $executable @($versionArguments[$package.Tool]) 2>&1
    if ($LASTEXITCODE -ne 0 -or -not $versionOutput) {
        throw "$($package.Tool) executable probe failed: $executable"
    }
    Write-Host "$($package.Tool): $(@($versionOutput)[0])"
}

if ($env:GITHUB_PATH) {
    $toolDirectories = @(
        $packages |
            ForEach-Object { Resolve-Tool $_.Tool } |
            Where-Object { $_ } |
            ForEach-Object { Split-Path -Parent $_ } |
            Sort-Object -Unique
    )
    foreach ($directory in $toolDirectories) {
        Add-Content -LiteralPath $env:GITHUB_PATH -Value $directory -Encoding utf8
    }
}

Write-Host 'Media tools ready: ffmpeg, tesseract, exiftool'
