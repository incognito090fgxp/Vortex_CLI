@echo off
setlocal
:: Get the directory of the script
set "BASE_DIR=%~dp0"
set "VENV_PYTHON=%BASE_DIR%venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -m vortex.core.cli %*
) else (
    echo [ERROR] Virtual environment not found at %BASE_DIR%venv
    echo Please run: python -m venv venv ^&^& .\venv\Scripts\activate ^&^& pip install -e .
    pause
)
endlocal
