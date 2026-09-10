$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) { python -m venv .venv }
& ./.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& ./.venv/Scripts/python.exe scripts/build_manifest.py
& ./.venv/Scripts/python.exe -m alembic -c backend/alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Migration failed' }
Push-Location backend
& ../.venv/Scripts/python.exe -m app.cli ingest
& ../.venv/Scripts/python.exe -m app.cli reference-release
Pop-Location
Push-Location frontend
cmd /c npm ci
Pop-Location
Write-Output 'Ready. See README for the two local server commands and optional remote corpus acquisition.'
