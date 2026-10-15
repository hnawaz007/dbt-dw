@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  ETL Pipeline UI Launcher
REM  Opens Airbyte-style dashboard at http://localhost:8080
REM ─────────────────────────────────────────────────────────────────────────────

echo.
echo Checking dependencies ...
python -c "import fastapi, uvicorn" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Installing dependencies from requirements_ui.txt ...
    pip install -r requirements_ui.txt
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies.
        pause & exit /b 1
    )
)

echo [OK] Dependencies ready.
echo.
echo Starting ETL Pipeline UI on http://localhost:8080 ...
echo Press Ctrl+C to stop.
echo.

REM Open browser after a short delay
start /b cmd /c "timeout /t 2 >nul && start http://localhost:8080"

REM Start the server
python -m uvicorn etl_ui:app --host 0.0.0.0 --port 8080

pause
