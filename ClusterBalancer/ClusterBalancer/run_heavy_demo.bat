@echo off
REM ClusterBalancer - Heavy Overload Demo (Batch Wrapper)
REM This batch file runs the PowerShell demo script with proper execution policy

echo ============================================================
echo  ClusterBalancer - Heavy Overload Demo (BATCH LAUNCHER)
echo ============================================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

REM Run the PowerShell script with ExecutionPolicy bypass
powershell -NoProfile -ExecutionPolicy Bypass -File ".\demo_overload.ps1"

REM Pause so user can see the output
pause
