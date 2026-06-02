@echo off
setlocal enabledelayedexpansion

echo Run PROJECT ...
echo.
REM Figlet is optional on Windows - just show a banner instead
echo  ================
echo   G A M   Y A R
echo  ================
echo.
echo STARTING ...
echo.

set /p GAP_API="Enter Your gap GPT API: "
set GAPGPT_API_KEY=%GAP_API%
echo Your API has been set.
echo.

REM install Virtual Enviroment Python


REM Activate virtual environment for Windows
python -m venv .venv
call .venv\Scripts\activate.bat
echo.

echo Checking libs ...
echo.

REM Function to check and install libraries
call :check_lib flask
call :check_lib requests
call :check_lib dotenv

echo.
echo Running Server...
cd ..
python server.py

REM Keep the window open if an error occurs
pause
exit /b

:check_lib
    pip show %~1 >nul 2>&1
    if %errorlevel% equ 0 (
        echo %~1 Installed ✓
    ) else (
        echo Installing %~1 ...
        pip install -i https://mirror-pypi.runflare.com/simple %~1
    )
goto :eof
