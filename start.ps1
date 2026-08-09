$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$EnvPath = Join-Path $ProjectRoot ".env"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Python environment was not found. Run setup.ps1 first."
}
if (-not (Test-Path -LiteralPath $EnvPath)) {
    throw ".env was not found. Create it before starting the application."
}

Set-Location -LiteralPath $ProjectRoot
$Existing = Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $Existing) {
    $Process = Start-Process -FilePath $PythonPath -ArgumentList "app.py" -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru
    $Ready = $false
    for ($Index = 0; $Index -lt 20; $Index++) {
        $Existing = Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($Existing) {
            $Ready = $true
            break
        }
        Start-Sleep -Milliseconds 500
    }
    if (-not $Ready) {
        if (-not $Process.HasExited) {
            Stop-Process -Id $Process.Id -Force
        }
        throw "The application did not start on port 5001."
    }
}

Start-Process "http://127.0.0.1:5001"
