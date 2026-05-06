$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot "web_backend"
$frontendDir = Join-Path $repoRoot "web_frontend"

Write-Host "Starting KLTT Web Demo..."
Write-Host "Backend: $backendDir"
Write-Host "Frontend: $frontendDir"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$backendDir`"; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$frontendDir`"; npm run dev"

Write-Host "Done. Open http://127.0.0.1:5173"

