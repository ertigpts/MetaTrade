$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPath = Join-Path $ProjectRoot ".venv"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"
$EnvPath = Join-Path $ProjectRoot ".env"
$EnvExamplePath = Join-Path $ProjectRoot ".env.example"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    & python -m venv $VenvPath
}

& $PythonPath -m pip install --upgrade pip
& $PythonPath -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
if (-not (Test-Path -LiteralPath $EnvPath) -and (Test-Path -LiteralPath $EnvExamplePath)) {
    Copy-Item -LiteralPath $EnvExamplePath -Destination $EnvPath
    Write-Host "Created .env from .env.example. Add your private keys before starting." -ForegroundColor Yellow
}
Write-Host "آماده شد. برای اجرا start.ps1 را اجرا کنید." -ForegroundColor Green
