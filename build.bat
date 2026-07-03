@echo off
echo =======================================================
echo Bhumi Billing - Windows Executable Compiling Script
echo =======================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system PATH. Please install Python.
    pause
    exit /b 1
)

:: 2. Check virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating local virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] No local virtual environment 'venv' found. Using system Python packages.
)

:: 3. Install dependencies
echo [INFO] Verifying development dependencies (PySide6, ReportLab, PyInstaller)...
python -m pip install --upgrade pip
python -m pip install PySide6 reportlab pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install application dependencies. Check internet connection.
    pause
    exit /b 1
)

:: 4. Run PyInstaller Compiler
echo.
echo [INFO] Starting PyInstaller compiling process...
echo [INFO] Building standalone onefile binary with hidden terminal console...
pyinstaller --noconsole --onefile --clean --name="BhumiBilling" main.py
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller compilation failed. Check logs above.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo [SUCCESS] Compilation completed successfully!
echo [INFO] Standalone executable is available inside: dist\BhumiBilling.exe
echo =======================================================
echo.
pause
