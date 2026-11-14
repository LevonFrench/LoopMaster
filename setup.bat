@echo off
setlocal
cd /d "%~dp0"

echo ===================================================
echo   LoopMaster setup
echo ===================================================
echo.

if /i "%~1"=="--help" goto :usage
if /i "%~1"=="/?" goto :usage

:: Keep this pin in step with stable-audio-3\pyproject.toml.
set "TORCH_PIN=torch==2.7.1 torchaudio==2.7.1"
set "TORCH_INDEX=https://download.pytorch.org/whl/cu126"
if /i "%~1"=="--cpu" set "TORCH_INDEX="

set "PY=stable-audio-3\.venv\Scripts\python.exe"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found on PATH. Install Python 3.10, 3.11 or 3.12 and run setup again.
    exit /b 1
)
python -c "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 12) else 1)"
if errorlevel 1 (
    echo Warning: LoopMaster is tested on Python 3.10 to 3.12. Yours is:
    python --version
    echo Continuing anyway.
    echo.
)

if not exist "%PY%" (
    echo [1/4] Creating the virtual environment in stable-audio-3\.venv
    python -m venv "stable-audio-3\.venv"
    if errorlevel 1 goto :failed
) else (
    echo [1/4] Using the existing virtual environment in stable-audio-3\.venv
)

"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto :failed

if defined TORCH_INDEX (
    echo [2/4] Installing PyTorch with CUDA 12.6. This is a large download.
    "%PY%" -m pip install %TORCH_PIN% --index-url %TORCH_INDEX%
) else (
    echo [2/4] Installing CPU-only PyTorch
    "%PY%" -m pip install %TORCH_PIN%
)
if errorlevel 1 goto :failed

echo [3/4] Installing Stable Audio 3 and the LoopMaster server
"%PY%" -m pip install -e stable-audio-3
if errorlevel 1 goto :failed
"%PY%" -m pip install -r "loopmaster\loopmaster-app\requirements.txt"
if errorlevel 1 goto :failed

echo.
echo [4/4] Model weights
echo   The weights come from Hugging Face under the Stability AI Community
echo   License: https://stability.ai/license
echo.
echo   [1] Medium         (GPU, best quality)
echo   [2] Small Music    (lightweight, CPU or GPU)
echo   [3] Small SFX      (sound effects)
echo   [4] Medium BF16    (community conversion, lower VRAM)
echo   [5] Skip for now
echo.
set "pick=1"
set /p pick="Download which model [1-5] (default 1): "
set "pick=%pick: =%"

set "MODEL="
if "%pick%"=="1" set "MODEL=medium"
if "%pick%"=="2" set "MODEL=small-music"
if "%pick%"=="3" set "MODEL=small-sfx"
if "%pick%"=="4" set "MODEL=medium-bf16"

if defined MODEL (
    "%PY%" scripts\download_models.py %MODEL%
    if errorlevel 1 (
        echo.
        echo The Python environment is installed, but the model is not downloaded yet.
        echo Fix the problem above, then run:
        echo   %PY% scripts\download_models.py %MODEL%
        exit /b 1
    )
) else (
    echo Skipped. Download a model later with:
    echo   %PY% scripts\download_models.py medium
)

echo.
echo Setup finished. Start LoopMaster with run_normal.bat, or run_server.bat
echo and open http://localhost:7861
exit /b 0

:usage
echo Usage: setup.bat [--cpu]
echo.
echo   Creates stable-audio-3\.venv, installs PyTorch, Stable Audio 3 and the
echo   LoopMaster server, then offers to download model weights.
echo.
echo   --cpu   Install CPU-only PyTorch instead of the CUDA 12.6 build.
exit /b 0

:failed
echo.
echo Setup stopped because the step above failed.
exit /b 1
