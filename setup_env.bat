@echo off
REM Setup script for Kelp Automated Deal Flow project
REM AI-ML GC 2025-26

echo ==========================================
echo  Kelp Automated Deal Flow - Environment Setup
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment
echo [1/4] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)
python -m venv venv

REM Activate virtual environment
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [3/4] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo [4/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo ==========================================
echo  Setup Complete!
echo ==========================================
echo.
echo To activate the environment, run:
echo     venv\Scripts\activate
echo.
echo To run the pipeline:
echo     python src\main.py
echo.
pause
