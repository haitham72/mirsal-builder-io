$ErrorActionPreference = 'Stop'
$mirsalEval = 'G:\Haitham\VsCode\Mirsal-Builder\mirsal\local_eval'
$mirsalDocs = 'G:\Haitham\VsCode\Mirsal-Builder\docs'
$mirsalChanges = Get-Content -LiteralPath "$mirsalEval\doc_updates\manifest.json" -Raw | ConvertFrom-Json
foreach ($mirsalChange in $mirsalChanges) {
    if ($mirsalChange.name -notin @('waiting-for-haitham.md', 'measurements.md')) { throw 'Unexpected document path.' }
    $mirsalTarget = Join-Path $mirsalDocs $mirsalChange.name
    $mirsalStaged = Join-Path "$mirsalEval\doc_updates" $mirsalChange.name
    if ((Get-FileHash -LiteralPath $mirsalTarget -Algorithm SHA256).Hash.ToLower() -ne $mirsalChange.original) { throw "Document changed since review: $mirsalTarget" }
    if ((Get-FileHash -LiteralPath $mirsalStaged -Algorithm SHA256).Hash.ToLower() -ne $mirsalChange.updated) { throw "Staged document changed: $mirsalStaged" }
}
foreach ($mirsalChange in $mirsalChanges) {
    $mirsalTarget = Join-Path $mirsalDocs $mirsalChange.name
    Copy-Item -LiteralPath (Join-Path "$mirsalEval\doc_updates" $mirsalChange.name) -Destination $mirsalTarget -Force
    if ((Get-FileHash -LiteralPath $mirsalTarget -Algorithm SHA256).Hash.ToLower() -ne $mirsalChange.updated) { throw "Copy verification failed: $mirsalTarget" }
    Write-Output "Updated and verified $mirsalTarget"
}
