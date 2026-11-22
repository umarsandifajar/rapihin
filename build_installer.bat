@echo off
setlocal
cd /d "%~dp0"

echo [1/2] Membuat executable (PyInstaller)...
call build.bat
if not exist "dist\rapihin.exe" (
    echo Gagal: dist\rapihin.exe tidak ditemukan.
    exit /b 1
)

echo.
echo [2/2] Mengompilasi installer (Inno Setup)...

set "ISCC="
if exist "C:\Program Files\Inno Setup 7\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 7\ISCC.exe"
if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 7\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 7\ISCC.exe"
if not defined ISCC if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    for /f "tokens=*" %%i in ('where ISCC.exe 2^>nul') do (
        set "ISCC=%%i"
        goto :found
    )
)

:found
if not defined ISCC (
    echo Error: Inno Setup Compiler ^(ISCC.exe^) tidak ditemukan.
    exit /b 1
)

"%ISCC%" installer.iss
if errorlevel 1 (
    echo Kompilasi installer gagal.
    exit /b 1
)

echo.
echo ========================================================
echo SUKSES! File installer ada di folder:
echo installer_output\
echo ========================================================
pause
