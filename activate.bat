@echo off
SET "VENV_DIR=%~dp0backend\venv"
SET "SCRIPTS_DIR=%VENV_DIR%\Scripts"

echo Checking Python installation...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

IF NOT EXIST "%VENV_DIR%" (
    echo Virtual environment not found in backend folder.
    echo Please create it first using: python -m venv backend/venv
    exit /b 1
)

echo Activating virtual environment and installing requirements...
cmd /k ""%SCRIPTS_DIR%\activate.bat" && python -m pip install --upgrade pip && pip install -r backend/requirements.txt && echo Setup completed successfully! && echo. && echo You can now run your application with: python server.py && echo. && echo To deactivate the virtual environment type: deactivate && cd backend"
