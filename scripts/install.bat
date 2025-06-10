@echo off
setlocal enabledelayedexpansion

:: Bugster CLI installer wrapper for Windows

:: ANSI color codes for Windows 10+
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

:: Enable ANSI escape sequences
reg query HKCU\Console /v VirtualTerminalLevel >nul 2>&1
if %ERRORLEVEL% neq 0 (
    reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1
)

:: Print functions
:print_step
echo.
echo %BLUE%=^> %~1%NC%
exit /b

:print_error
echo %RED%%~1%NC%
exit /b

:print_success
echo %GREEN%%~1%NC%
exit /b

:print_warning
echo %YELLOW%%~1%NC%
exit /b

:: Show help message
:show_help
echo Bugster CLI Installer
echo.
echo Usage:
echo     install.bat [options]
echo.
echo Options:
echo     -v, --version VERSION    Install specific version (e.g., v0.2.8, v0.2.8-beta.1)
echo     -h, --help              Show this help message
echo     -y, --yes              Automatic yes to prompts
echo.
echo Examples:
echo     install.bat                           # Install latest version
echo     install.bat -v v0.2.8                # Install specific version
echo     install.bat -v v0.2.8-beta.1         # Install beta version
echo     install.bat -y                       # Install with automatic yes to prompts
exit /b

:: Parse command line arguments
set "VERSION=latest"
set "AUTO_YES=false"
:parse_args
if "%~1"=="" goto :main
if /i "%~1"=="-h" (
    call :show_help
    exit /b 0
)
if /i "%~1"=="--help" (
    call :show_help
    exit /b 0
)
if /i "%~1"=="-v" (
    if "%~2"=="" (
        call :print_error "Version argument is missing"
        call :show_help
        exit /b 1
    )
    set "VERSION=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--version" (
    if "%~2"=="" (
        call :print_error "Version argument is missing"
        call :show_help
        exit /b 1
    )
    set "VERSION=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="-y" (
    set "AUTO_YES=true"
    shift
    goto :parse_args
)
if /i "%~1"=="--yes" (
    set "AUTO_YES=true"
    shift
    goto :parse_args
)
call :print_error "Unknown option: %~1"
call :show_help
exit /b 1

:find_best_python
:: Check Python 3.12
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%PROGRAMFILES%\Python312\python.exe"
    "%PROGRAMFILES(x86)%\Python312\python.exe"
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.12.exe"
) do (
    if exist %%p (
        set "PYTHON_PATH=%%p"
        exit /b 0
    )
)

:: Check Python 3.11
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%PROGRAMFILES%\Python311\python.exe"
    "%PROGRAMFILES(x86)%\Python311\python.exe"
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.11.exe"
) do (
    if exist %%p (
        set "PYTHON_PATH=%%p"
        exit /b 0
    )
)

:: Check Python 3.10
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%PROGRAMFILES%\Python310\python.exe"
    "%PROGRAMFILES(x86)%\Python310\python.exe"
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.10.exe"
) do (
    if exist %%p (
        set "PYTHON_PATH=%%p"
        exit /b 0
    )
)

:: Check generic Python3
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('where python3') do set "PYTHON_PATH=%%i"
    exit /b 0
)

:: Check generic Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('where python') do set "PYTHON_PATH=%%i"
    exit /b 0
)

exit /b 1

:check_python_version
set "PYTHON_EXE=%~1"
"%PYTHON_EXE%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
exit /b %ERRORLEVEL%

:install_python
call :print_step "Installing Python 3.12..."

:: Check if winget is available
winget --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :print_step "Using winget to install Python 3.12..."
    winget install Python.Python.3.12 -h --accept-source-agreements --accept-package-agreements
    
    :: Wait for installation to complete
    timeout /t 5 >nul
    
    :: Update PATH
    set "PYTHON_INSTALL_DIR=%LOCALAPPDATA%\Programs\Python\Python312"
    set "SCRIPTS_DIR=%PYTHON_INSTALL_DIR%\Scripts"
    
    :: Create python.bat wrapper
    echo @echo off > "%PYTHON_INSTALL_DIR%\python.bat"
    echo "%PYTHON_INSTALL_DIR%\python.exe" %%* >> "%PYTHON_INSTALL_DIR%\python.bat"
    
    :: Create python3.bat wrapper
    echo @echo off > "%PYTHON_INSTALL_DIR%\python3.bat"
    echo "%PYTHON_INSTALL_DIR%\python.exe" %%* >> "%PYTHON_INSTALL_DIR%\python3.bat"
    
    :: Create pip.bat wrapper
    echo @echo off > "%PYTHON_INSTALL_DIR%\pip.bat"
    echo "%PYTHON_INSTALL_DIR%\python.exe" -m pip %%* >> "%PYTHON_INSTALL_DIR%\pip.bat"
    
    :: Create pip3.bat wrapper
    echo @echo off > "%PYTHON_INSTALL_DIR%\pip3.bat"
    echo "%PYTHON_INSTALL_DIR%\python.exe" -m pip %%* >> "%PYTHON_INSTALL_DIR%\pip3.bat"
    
    :: Add to PATH
    powershell -Command "$path = [Environment]::GetEnvironmentVariable('PATH', 'User'); if ($path -notlike '*%PYTHON_INSTALL_DIR%*') { [Environment]::SetEnvironmentVariable('PATH', '%PYTHON_INSTALL_DIR%;%SCRIPTS_DIR%;' + $path, 'User') }"
    
    :: Refresh PATH
    set "PATH=%PYTHON_INSTALL_DIR%;%SCRIPTS_DIR%;%PATH%"
    
    :: Verify installation
    "%PYTHON_INSTALL_DIR%\python.exe" --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        call :print_success "✅ Python 3.12 installed successfully!"
        set "PYTHON_PATH=%PYTHON_INSTALL_DIR%\python.exe"
        exit /b 0
    ) else (
        call :print_error "❌ Python 3.12 installation failed"
        exit /b 1
    )
) else (
    call :print_error "❌ Winget is not available. Please install Python 3.12 manually from https://www.python.org/downloads/"
    exit /b 1
)

:main
call :print_step "Checking Python installation..."

:: Find best Python version
call :find_best_python
if %ERRORLEVEL% EQU 0 (
    call :check_python_version "%PYTHON_PATH%"
    if %ERRORLEVEL% EQU 0 (
        for /f "tokens=*" %%i in ('"%PYTHON_PATH%" --version') do set PYTHON_VERSION=%%i
        call :print_success "✅ %PYTHON_VERSION% is installed, continuing with installation..."
    ) else (
        call :print_error "❌ Python 3.10 or higher is required"
        if "%AUTO_YES%"=="true" (
            set "choice=Y"
        ) else (
            call :print_warning "Would you like to install Python 3.12? (Y/N)"
            set /p choice="> "
        )
        if /i "!choice!"=="Y" (
            call :install_python
            if %ERRORLEVEL% NEQ 0 exit /b 1
        ) else (
            call :print_error "Please install Python 3.10 or higher manually and try again."
            exit /b 1
        )
    )
) else (
    call :print_error "❌ Python is not installed"
    if "%AUTO_YES%"=="true" (
        set "choice=Y"
    ) else (
        call :print_warning "Would you like to install Python 3.12? (Y/N)"
        set /p choice="> "
    )
    if /i "!choice!"=="Y" (
        call :install_python
        if %ERRORLEVEL% NEQ 0 exit /b 1
    ) else (
        call :print_error "Please install Python 3.10 or higher manually and try again."
        exit /b 1
    )
)

:: Download and run the Python installer script
call :print_step "Downloading the Bugster CLI installer..."
if "%VERSION%"=="latest" (
    curl -sSL https://raw.githubusercontent.com/Bugsterapp/bugster-cli/main/scripts/install.py > "%TEMP%\bugster_install.py"
    "%PYTHON_PATH%" "%TEMP%\bugster_install.py"
) else (
    curl -sSL https://raw.githubusercontent.com/Bugsterapp/bugster-cli/main/scripts/install.py > "%TEMP%\bugster_install.py"
    "%PYTHON_PATH%" "%TEMP%\bugster_install.py" --version "%VERSION%"
)

set EXIT_CODE=%ERRORLEVEL%
del "%TEMP%\bugster_install.py"

if %EXIT_CODE% EQU 0 (
    call :print_warning "Please add the Bugster installation directory to your PATH if not already added:"
    echo %LOCALAPPDATA%\Programs\bugster
    echo.
    call :print_success "To use Bugster CLI, run: bugster --help"
)

pause
exit /b %EXIT_CODE% 