$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "multi_asset_research.py"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python environment is missing. Run Setup-MetaTrader5.bat first."
}

$Runs = @(
    @{ Interval = "4h"; Output = "multi-asset-research-latest.json" },
    @{ Interval = "1h"; Output = "multi-asset-research-h1.json" },
    @{ Interval = "15min"; Output = "multi-asset-research-m15.json" }
)
foreach ($Run in $Runs) {
    $Report = Join-Path $ProjectRoot ("data\" + $Run.Output)
    & $Python $Script --interval $Run.Interval --candles 5000 --output $Report
    if ($LASTEXITCODE -ne 0) {
        throw "Research failed for $($Run.Interval) with exit code $LASTEXITCODE."
    }
}

Write-Host "Multi-asset research reports are ready in $ProjectRoot\data"
