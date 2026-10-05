$ErrorActionPreference = 'Stop'
$stage = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'chains-seed'))
$target = [IO.Path]::GetFullPath('G:\Haitham\VsCode\Mirsal-Builder\faq')
if ($target -ne 'G:\Haitham\VsCode\Mirsal-Builder\faq') { throw 'Unexpected FAQ target' }
$files = @(Get-ChildItem -LiteralPath $stage -Recurse -File -Filter '*.md')
if ($files.Count -ne 21) { throw 'Expected 21 additional FAQ files' }
foreach ($file in $files) {
    $dest = [IO.Path]::GetFullPath((Join-Path $target $file.FullName.Substring($stage.Length + 1)))
    if (-not $dest.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'FAQ path escaped target' }
    if ((Test-Path -LiteralPath $dest) -and (Get-FileHash -LiteralPath $dest).Hash -ne (Get-FileHash -LiteralPath $file.FullName).Hash) {
        throw "Existing FAQ differs: $dest"
    }
}
foreach ($file in $files) {
    $dest = Join-Path $target $file.FullName.Substring($stage.Length + 1)
    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
    if ((Get-FileHash -LiteralPath $dest).Hash -ne (Get-FileHash -LiteralPath $file.FullName).Hash) { throw "Copy differs: $dest" }
}
Write-Output 'Installed and hash-checked 21 additional root FAQ files; existing entries preserved.'
