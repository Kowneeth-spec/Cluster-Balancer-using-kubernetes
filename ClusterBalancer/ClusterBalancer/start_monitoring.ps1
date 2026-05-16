# ClusterBalancer - Continuous Monitoring Launcher (PowerShell)
# Runs monitoring with easy stop/start

param(
    [int]$Interval = 30,
    [switch]$Background = $false,
    [string]$LogFile = "monitor_log.txt"
)

$ProjectPath = "c:\Users\kowne\Downloads\Drive\CPP Mini Project\ClusterBalancer\ClusterBalancer"
Set-Location $ProjectPath

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ClusterBalancer - Continuous Monitoring" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Interval: $Interval seconds"
Write-Host "  Log file: $LogFile"
Write-Host "  Background: $Background"
Write-Host ""
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Green
Write-Host ""

# Add timestamp to log
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$timestamp] Monitoring started"

# Run monitoring
if ($Background) {
    Write-Host "Starting background monitoring..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-Command `"cd '$ProjectPath'; python monitoring/monitor.py --continuous --interval $Interval | Tee-Object -Append -FilePath '$LogFile'`"" -NoNewWindow
    Write-Host "Monitoring running in background. Check $LogFile for updates." -ForegroundColor Green
} else {
    Write-Host "Starting continuous monitoring..." -ForegroundColor Green
    python monitoring/monitor.py --continuous --interval $Interval | Tee-Object -Append -FilePath $LogFile
}

Write-Host ""
Write-Host "Monitoring stopped." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$timestamp] Monitoring stopped"
