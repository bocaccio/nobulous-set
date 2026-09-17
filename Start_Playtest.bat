@echo off
setlocal
cd /d "%~dp0"

set "PORT=8000"
set "WEBROOT=%~dp0playtest\dist"

if not exist "%WEBROOT%\index.html" (
    echo.
    echo ERROR: The playtest files were not found.
    echo Keep Start_Playtest.bat inside the extracted nobulous-set folder.
    echo Expected file: "%WEBROOT%\index.html"
    echo.
    pause
    exit /b 1
)

rem Find Python, including common Miniforge installations that are not on PATH.
set "PYTHON_EXE="
set "PYTHON_ARGS="

if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PYTHON_EXE=%CONDA_PREFIX%\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniforge3\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniforge3\python.exe"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\miniforge3\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\miniforge3\python.exe"
if not defined PYTHON_EXE if exist "%ProgramData%\miniforge3\python.exe" set "PYTHON_EXE=%ProgramData%\miniforge3\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe"

if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
)

if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('where py 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
    if defined PYTHON_EXE set "PYTHON_ARGS=-3"
)

if not defined PYTHON_EXE (
    echo.
    echo ERROR: Python could not be found.
    echo.
    echo Open the Miniforge Prompt, change to this folder, and run:
    echo     Start_Playtest.bat
    echo.
    echo The launcher also checks these common locations:
    echo     %USERPROFILE%\miniforge3
    echo     %LOCALAPPDATA%\miniforge3
    echo     %ProgramData%\miniforge3
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" %PYTHON_ARGS% -c "import sys" >nul 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: Python was found but could not be started.
    echo Python: "%PYTHON_EXE%" %PYTHON_ARGS%
    echo Try opening a Miniforge Prompt and running Start_Playtest.bat there.
    echo.
    pause
    exit /b 1
)

echo.
echo Starting Nobulous Playtest Lab
echo Address: http://localhost:%PORT%/
echo Python:  "%PYTHON_EXE%"
echo.
echo Your browser should open automatically.
echo If it does not, open http://localhost:%PORT%/ yourself.
echo Leave this window open while playing.
echo Press Ctrl+C here to stop the server.
echo.

rem Open the browser after the server has had time to start. Use Windows' URL
rem handler directly; PowerShell Start-Process can be blocked on some systems.
start "" /B "%ComSpec%" /d /c "ping -n 3 127.0.0.1 >nul & start http://localhost:%PORT%/"
"%PYTHON_EXE%" %PYTHON_ARGS% -m http.server %PORT% --directory "%WEBROOT%"
set "SERVER_EXIT=%ERRORLEVEL%"

echo.
if not "%SERVER_EXIT%"=="0" (
    echo ERROR: The playtest server stopped with code %SERVER_EXIT%.
    echo If port %PORT% is already in use, close the other server and try again.
) else (
    echo The playtest server has stopped.
)
echo.
pause
exit /b %SERVER_EXIT%
