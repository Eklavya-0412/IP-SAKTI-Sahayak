# Run in Codex's bundled presentation runtime. Ordinary deployment does not need it.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$taskBuild = Join-Path $projectRoot 'tmp/deck'
New-Item -ItemType Directory -Force $taskBuild | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'build_deck.mjs') -Destination (Join-Path $taskBuild 'build.mjs')
$runtimePackages = 'C:\Users\Rushabh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
if (-not (Test-Path (Join-Path $taskBuild 'node_modules'))) { New-Item -ItemType Junction -Path (Join-Path $taskBuild 'node_modules') -Target $runtimePackages | Out-Null }
Write-Output 'The presentation finalizer refuses to overwrite a final file or receipt. Choose new output/receipt names in build_deck.mjs for a revised submission.'
& 'C:\Users\Rushabh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' (Join-Path $taskBuild 'build.mjs')
