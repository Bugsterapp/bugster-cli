@echo off
setlocal

:: This is a wrapper to download and execute the main PowerShell installer.
:: It forwards all command-line arguments to the PowerShell script.
set "SCRIPT_URL=https://raw.githubusercontent.com/Bugsterapp/bugster-cli/main/scripts/install.ps1"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('%SCRIPT_URL%'))" %*

endlocal 
