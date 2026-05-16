@echo off
REM ClusterBalancer - Continuous Monitoring Launcher
REM Runs monitoring in the background and logs to file

setlocal enabledelayedexpansion

cd /d "c:\Users\kowne\Downloads\Drive\CPP Mini Project\ClusterBalancer\ClusterBalancer"

echo.
echo ========================================
echo ClusterBalancer - Continuous Monitoring
echo ========================================
echo.
echo Monitoring will run in background
echo Logs saved to: monitor_log.txt
echo Press Ctrl+C in the console to stop
echo.

REM Create timestamp for log
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)

echo [%mydate% %mytime%] Monitoring started >> monitor_log.txt

REM Run continuous monitoring and append to log
python monitoring/monitor.py --continuous --interval 30 >> monitor_log.txt 2>&1

echo.
echo [%date% %time%] Monitoring stopped >> monitor_log.txt
echo Monitoring stopped. Check monitor_log.txt for details.
