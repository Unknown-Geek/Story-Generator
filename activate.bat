@echo off
SET "VENV_DIR=%~dp0venv"
SET "SCRIPTS_DIR=%VENV_DIR%\Scripts"

echo Checking Python installation...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

IF NOT EXIST "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment
        exit /b 1
    )
)

echo Installing requirements...
cmd /k ""%SCRIPTS_DIR%\activate.bat" && python -m pip install --upgrade pip && pip install -r requirements.txt && echo Setup completed successfully! && echo. && echo You can now run your application with: python app.py && echo. && echo To deactivate the virtual environment type: deactivate"
