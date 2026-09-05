# ==============================================================================
# TheBoringEnglish Desktop Client PowerShell 启动脚本
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "TheBoringEnglish Client"

Set-Location -LiteralPath $PSScriptRoot

Write-Host "Starting TheBoringEnglish Client..." -ForegroundColor Cyan

& python -m src.main

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[Error] Client exited with error code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host "Please ensure all dependencies are installed: pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host "Press any key to exit..."
    [Console]::ReadKey() | Out-Null
}


