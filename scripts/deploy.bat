@echo off
REM AI Data Matching Tool - Windows Deployment Script
REM This script provides multiple ways to set the OpenAI API key

echo.
echo 🚀 AI Data Matching Tool - Deployment Script
echo =============================================

:menu
echo.
echo Choose deployment method:
echo 1) Use existing OPENAI_API_KEY environment variable
echo 2) Create/use .env file
echo 3) Enter API key now (will be visible)
echo 4) Run without API key (for testing - LLM features disabled)
echo.

set /p choice="Select option (1-4): "

if "%choice%"=="1" goto env_var
if "%choice%"=="2" goto env_file
if "%choice%"=="3" goto prompt
if "%choice%"=="4" goto no_key
goto invalid

:env_var
if "%OPENAI_API_KEY%"=="" (
    echo ❌ OPENAI_API_KEY environment variable not set
    echo Set it with: set OPENAI_API_KEY=your-key-here
    pause
    exit /b 1
)
echo ✅ Using OPENAI_API_KEY from environment
docker-compose up -d
goto success

:env_file
if not exist .env (
    echo 📝 Creating .env file...
    set /p api_key="Enter your OpenAI API Key: "
    echo OPENAI_API_KEY=%api_key%> .env
    echo ✅ Created .env file
)
docker-compose up -d
goto success

:prompt
set /p api_key="Enter your OpenAI API Key: "
set OPENAI_API_KEY=%api_key%
docker-compose up -d
goto success

:no_key
echo ⚠️  Deploying without OpenAI API key - LLM features will be disabled
docker-compose up -d
goto success

:invalid
echo ❌ Invalid choice
goto menu

:success
echo.
echo 🎉 Deployment complete!
echo 🌐 Application available at: http://localhost:8503
echo 🔍 Check status: docker-compose ps
echo 📋 View logs: docker-compose logs -f
echo 🛑 Stop: docker-compose down
pause