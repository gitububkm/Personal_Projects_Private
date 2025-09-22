@echo off
setlocal

set APPDIR=%ProgramData%\SimpleTrialApp
mkdir "%APPDIR%" 2>nul

echo Copying files...
copy "%~dp0app.py" "%APPDIR%\" >nul
copy "%~dp0uninstaller.bat" "%APPDIR%\" >nul
copy "%~dp0installer.bat" "%APPDIR%\" >nul

if not exist "%APPDIR%\info.json" (
    echo {"first_install_ts": null, "time_limit_seconds": 60, "start_limit": 2, "starts_used": 0, "removed_completely": false} > "%APPDIR%\info.json"
)

reg add "HKCU\Software\SimpleTrialApp" /v InstallPath /t REG_SZ /d "%APPDIR%" /f >nul

echo Installation complete. Folder: %APPDIR%
pause
endlocal
