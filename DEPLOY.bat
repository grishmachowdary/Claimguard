@echo off
REM ClaimGuard V2 Quick Deployment Script for Windows

setlocal enabledelayedexpansion

echo.
echo 🚀 ClaimGuard V2 Production Deployment
echo ======================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)
echo ✓ Python found

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 14+
    exit /b 1
)
echo ✓ Node.js found
echo.

REM Backend setup
echo Setting up Backend...
cd backend

echo Installing Python dependencies...
pip install -r requirements.txt >nul 2>&1

echo Downloading spaCy model (this may take a minute)...
python -m spacy download en_core_web_sm >nul 2>&1

echo ✓ Backend dependencies installed
cd ..
echo.

REM Frontend setup
echo Setting up Frontend...
cd frontend

echo Installing Node dependencies...
call npm install >nul 2>&1

echo Building production bundle...
call npm run build >nul 2>&1

echo ✓ Frontend built
cd ..
echo.

REM Summary
echo ======================================
echo ✅ ClaimGuard V2 Ready for Deployment
echo ======================================
echo.

echo 📋 Next Steps:
echo.
echo 1. Configure environment:
echo    copy backend\.env.example backend\.env
echo    (Edit backend\.env with production settings)
echo.
echo 2. Start Backend (choose one):
echo    Option A - Development:
echo      cd backend
echo      python app.py
echo.
echo    Option B - Production:
echo      cd backend
echo      pip install gunicorn
echo      gunicorn -w 4 -b 0.0.0.0:5000 app:app
echo.
echo 3. Serve Frontend:
echo    cd frontend
echo    npm install -g serve
echo    serve -s build -l 3000
echo.
echo 4. Test:
echo    Open browser: http://localhost:3000
echo    Login: customer@test.com / password123
echo.
echo 📖 Full guide: V2_PRODUCTION_DEPLOYMENT.md
echo.

pause
