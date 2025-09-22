@echo off
setlocal

set APPDIR=%ProgramData%\SimpleTrialApp

if /I "%~1"=="/full" goto full

echo Standard uninstall: application will be removed, but trial data (info.json, names.txt) will remain.
pause
del "%APPDIR%\app.py" 2>nul
del "%APPDIR%\installer.bat" 2>nul
del "%APPDIR%\uninstaller.bat" 2>nul
reg delete "HKCU\Software\SimpleTrialApp" /v InstallPath /f >nul 2>nul
echo Program removed. Trial data preserved.
pause
goto end

:full
echo Full uninstall: removing all trial data!
del "%APPDIR%\*" /Q 2>nul
rmdir "%APPDIR%" 2>nul
reg delete "HKCU\Software\SimpleTrialApp" /f >nul 2>nul
echo Done. All traces removed.
pause

:end
endlocal
