$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[1/3] Backend smoke test"
Set-Location $repoRoot
python -m pytest web_backend/tests/smoke_test.py -q
if ($LASTEXITCODE -ne 0) {
  throw "Backend smoke test failed."
}

Write-Host "[2/3] Frontend build"
Set-Location (Join-Path $repoRoot "web_frontend")
npm run build
if ($LASTEXITCODE -ne 0) {
  throw "Frontend build failed."
}

Write-Host "[3/3] Backend quick health check"
Set-Location $repoRoot
@'
from fastapi.testclient import TestClient
from web_backend.app.main import app
with TestClient(app) as client:
    assert client.get('/health').status_code == 200
    assert client.get('/stats').status_code == 200
    assert client.get('/benchmark').status_code == 200
print("health-check-ok")
'@ | python -
if ($LASTEXITCODE -ne 0) {
  throw "Backend quick health check failed."
}

Write-Host "Quality gate passed."
