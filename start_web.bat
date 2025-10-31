@echo off
echo ===============================================
echo   PyPotteryLayout - Flask Web Application
echo ===============================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Please make sure Python is installed correctly
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
echo.
echo Checking dependencies...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo ===============================================
echo   Starting Flask Application
echo ===============================================
echo.
echo The application will be available at:
echo   http://localhost:5001
echo.
echo Press Ctrl+C to stop the server
echo ===============================================
echo.

python app.py

pause
