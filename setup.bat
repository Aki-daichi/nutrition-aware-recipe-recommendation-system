@echo off
REM Quick setup script for Windows

echo.
echo ====================================================
echo Nutrition-Aware Recipe Recommendation System - Setup
echo ====================================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

python --version
echo.

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
    echo.
) else (
    echo Virtual environment already exists
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Dependencies installed
echo.

REM Copy environment file
if not exist ".env" (
    copy .env.example .env
    echo Created .env file (edit with your database credentials)
    echo.
) else (
    echo .env file already exists
    echo.
)

REM Initialize database
echo Initializing database...
python -c "from backend.database import init_db; init_db()"
echo Database initialized
echo.

REM Seed sample data
echo Seeding database with sample data...
python seed_db.py
echo Sample data added
echo.

echo ====================================================
echo Setup completed successfully!
echo ====================================================
echo.
echo Next steps:
echo 1. Edit .env file with your database credentials (if needed)
echo 2. Run the server: python backend/main.py
echo 3. Visit: http://localhost:8000/dashboard
echo.
echo To activate virtual environment in future:
echo   venv\Scripts\activate.bat
echo ====================================================
echo.
pause
