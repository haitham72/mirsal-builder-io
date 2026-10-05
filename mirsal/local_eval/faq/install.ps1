$ErrorActionPreference = 'Stop'
$stage = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'seed'))
$target = [IO.Path]::GetFullPath('G:\Haitham\VsCode\Mirsal-Builder\faq')
if ($target -ne 'G:\Haitham\VsCode\Mirsal-Builder\faq') { throw 'Unexpected FAQ target' }
$files = @(Get-ChildItem -LiteralPath $stage -Recurse -File -Filter '*.md')
if ($files.Count -ne 66) { throw 'Expected 66 staged FAQ files' }
foreach ($file in $files) {
    $relative = $file.FullName.Substring($stage.Length + 1)
    $dest = [IO.Path]::GetFullPath((Join-Path $target $relative))
    if (-not $dest.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'FAQ path escaped target' }
    if (Test-Path -LiteralPath $dest) {
        if ((Get-FileHash -LiteralPath $dest).Hash -ne (Get-FileHash -LiteralPath $file.FullName).Hash) { throw "Different existing FAQ: $relative" }
    }
}
foreach ($file in $files) {
    $relative = $file.FullName.Substring($stage.Length + 1)
    $dest = Join-Path $target $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
    if ((Get-FileHash -LiteralPath $dest).Hash -ne (Get-FileHash -LiteralPath $file.FullName).Hash) { throw "Copy differs: $relative" }
}
Write-Output 'Installed and hash-checked 66 FAQ files at repository root.'
