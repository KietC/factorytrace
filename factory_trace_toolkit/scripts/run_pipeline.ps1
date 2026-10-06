# English: Run ingestion, query generation, assessment, reports, and gates on an initialized case.
# 中文：对已初始化案件依次执行采集、检索词、评估、报告与门槛；必须声明模型模式，材料或审计缺口只保留线索结论。
param(
    [Parameter(Mandatory = $true)]
    [string]$CaseRoot,
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,
    [string]$PrimaryImage = '',
    [ValidateSet('undeclared', 'none', 'cloud', 'local', 'hybrid')]
    [string]$ModelMode = 'undeclared',
    [string]$ModelId = ''
)

$ErrorActionPreference = 'Stop'
$ToolkitRoot = Split-Path -Parent $PSScriptRoot
$FactoryTrace = Join-Path $ToolkitRoot '.venv\Scripts\factorytrace.exe'

function Assert-NativeSuccess {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

if (-not (Test-Path -LiteralPath $FactoryTrace)) {
    throw 'Run scripts\bootstrap.ps1 first.'
}
if ($ModelMode -eq 'undeclared') {
    throw 'Declare -ModelMode none|cloud|local|hybrid before running the case.'
}

$DoctorArgs = @(
    'doctor',
    '--case-root', $CaseRoot,
    '--model-mode', $ModelMode
)
if ($ModelId) {
    $DoctorArgs += @('--model-id', $ModelId)
}
& $FactoryTrace @DoctorArgs
Assert-NativeSuccess 'Capture case environment and model mode'

& $FactoryTrace ingest $SourcePath --recursive --case-root $CaseRoot --workers 8
Assert-NativeSuccess 'Ingest source artifacts'

if ($PrimaryImage) {
    & $FactoryTrace variants $PrimaryImage --case-root $CaseRoot --crop-plan (Join-Path $CaseRoot 'work\crop_plan.json')
    Assert-NativeSuccess 'Generate image variants'
}

& $FactoryTrace queries --profile (Join-Path $CaseRoot 'work\product_profile.json') --case-root $CaseRoot
Assert-NativeSuccess 'Generate search queries'

& $FactoryTrace ledger --case-root $CaseRoot
Assert-NativeSuccess 'Regenerate canonical evidence ledger'
& $FactoryTrace validate --case-root $CaseRoot
Assert-NativeSuccess 'Validate schema v2 and semantic invariants'
& $FactoryTrace assess --case-root $CaseRoot
Assert-NativeSuccess 'Compute multi-axis assessments'
& $FactoryTrace hypotheses --case-root $CaseRoot
Assert-NativeSuccess 'Build H1-H5 ACH matrix'
& $FactoryTrace report --case-root $CaseRoot --format 'md,json,csv,xlsx,docx'
Assert-NativeSuccess 'Generate all report formats'
& $FactoryTrace lint-report --case-root $CaseRoot
Assert-NativeSuccess 'Lint report semantics'
& $FactoryTrace audit --case-root $CaseRoot --stage research
Assert-NativeSuccess 'Run research audit'

& $FactoryTrace materials --case-root $CaseRoot --stage discovery
$MaterialsExit = $LASTEXITCODE
& $FactoryTrace audit --case-root $CaseRoot --stage operational
$OperationalExit = $LASTEXITCODE
if ($MaterialsExit -ne 0 -or $OperationalExit -ne 0) {
    throw "Evidence gate incomplete: materials exit=$MaterialsExit; operational audit exit=$OperationalExit. Reports were generated as leads only."
}
