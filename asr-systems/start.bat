@echo off
title ASR Production Server
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   ASR Invoice Archive System - Production Server
echo ============================================================
echo.

:: Check for Python
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or later from https://python.org
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo Found Python %PYVER%

:: Check for virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat

    echo Installing dependencies...
    pip install -r production-server\requirements.txt
)

:: Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo WARNING: .env file not found, copying from .env.example
        copy .env.example .env
        echo Please edit .env and set your ANTHROPIC_API_KEY
        pause
    ) else (
        echo WARNING: No .env or .env.example found
    )
)

:: Check if start_server.py exists
if exist "start_server.py" (
    echo.
    echo Starting ASR Production Server...
    echo.
    python start_server.py
) else (
    echo.
    echo Starting ASR Production Server via uvicorn...
    echo.
    python -m uvicorn production-server.api.main:app --host 0.0.0.0 --port 8000
)

if errorlevel 1 (
    echo.
    echo Server exited with error. Check logs for details.
    pause
)
