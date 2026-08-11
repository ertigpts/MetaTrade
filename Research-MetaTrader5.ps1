$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Report = Join-Path $ProjectRoot "data\research-latest.json"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python environment is missing. Run Setup-MetaTrader5.bat first."
}

& $Python (Join-Path $ProjectRoot "strategy_research.py") `
    --symbols "XAU/USD" `
    --intervals 1h 4h `
    --candles 5000 `
    --output $Report

if ($LASTEXITCODE -ne 0) {
    throw "Strategy research failed with exit code $LASTEXITCODE."
}

Write-Host "Research report: $Report"
