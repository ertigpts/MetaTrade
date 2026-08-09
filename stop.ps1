$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExpectedLauncher = (Join-Path $ProjectRoot ".venv\Scripts\python.exe").ToLowerInvariant()
$Listener = Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $Listener) {
    Write-Host "The local application is not running." -ForegroundColor Yellow
    exit 0
}

$Child = Get-CimInstance Win32_Process -Filter "ProcessId=$($Listener.OwningProcess)"
$Parent = if ($Child) { Get-CimInstance Win32_Process -Filter "ProcessId=$($Child.ParentProcessId)" } else { $null }
$ChildLooksRight = $Child -and $Child.Name -eq "python.exe" -and $Child.CommandLine -match "app\.py"
$ParentLooksRight = $Parent -and $Parent.ExecutablePath -and $Parent.ExecutablePath.ToLowerInvariant() -eq $ExpectedLauncher

if (-not ($ChildLooksRight -and $ParentLooksRight)) {
    throw "The process on port 5001 was not identified as this application and was not stopped."
}

Stop-Process -Id $Child.ProcessId -Force
if (Get-Process -Id $Parent.ProcessId -ErrorAction SilentlyContinue) {
    Stop-Process -Id $Parent.ProcessId -Force
}
$Closed = $false
for ($Index = 0; $Index -lt 20; $Index++) {
    Start-Sleep -Milliseconds 250
    $Remaining = Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $Remaining) {
        $Closed = $true
        break
    }
}
if (-not $Closed) {
    throw "Port 5001 did not close after stopping the application."
}
Write-Host "The local application was stopped." -ForegroundColor Green
