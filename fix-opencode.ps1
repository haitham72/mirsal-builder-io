# Clear OpenCode internal state to reclaim ports 49374/49375
# Run this script, then try: opencode serve --port 49375

Write-Host "Stopping any OpenCode processes..." -ForegroundColor Yellow
Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*opencode*" -or $_.CommandLine -like "*opencode*" } | Stop-Process -Force

Write-Host "Clearing OpenCode cache..." -ForegroundColor Yellow
$opencodeCache = "$env:USERPROFILE\.opencode"
if (Test-Path $opencodeCache) {
    Remove-Item -Path $opencodeCache -Recurse -Force
    Write-Host "Removed: $opencodeCache" -ForegroundColor Green
}

Write-Host "Clearing OpenCode config..." -ForegroundColor Yellow
$opencodeConfig = "$env:APPDATA\opencode"
if (Test-Path $opencodeConfig) {
    Remove-Item -Path $opencodeConfig -Recurse -Force
    Write-Host "Removed: $opencodeConfig" -ForegroundColor Green
}

Write-Host "Done. Try: opencode serve --port 49375" -ForegroundColor Cyan
