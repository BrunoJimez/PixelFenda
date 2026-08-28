@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_LAUNCHER=py
) else (
    set PYTHON_LAUNCHER=python
)

if not exist .venv (
    %PYTHON_LAUNCHER% -m venv .venv
    if errorlevel 1 (
        echo.
        echo Nao foi possivel criar o ambiente virtual. Verifique se o Python 3.11 ou 3.12 esta instalado.
        pause
        exit /b 1
    )
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERRO durante a instalacao.
    pause
    exit /b 1
)
echo.
echo PixelFenda instalado com sucesso.
echo Execute run_windows.bat
pause
