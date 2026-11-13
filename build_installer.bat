@echo off
setlocal

if not exist "dist\rapihin.exe" (
  echo [!] dist\rapihin.exe belum ada. Jalankan build.bat dulu.
  pause
  exit /b 1
)

set "ISCC="
rem Inno Setup 6 (lokasi umum)
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
rem Inno Setup 7 (diutamakan kalau ada)
if exist "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 7\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 7\ISCC.exe"
rem Cadangan: cari di PATH
if "%ISCC%"=="" for /f "delims=" %%P in ('where ISCC.exe 2^>nul') do set "ISCC=%%P"

if "%ISCC%"=="" (
  echo [!] ISCC.exe tidak ketemu. Pastikan Inno Setup 6 atau 7 sudah terinstall.
  echo     Alternatif manual: buka installer.iss di Inno Setup, lalu tekan Ctrl+F9 ^(Compile^).
  pause
  exit /b 1
)

echo Memakai: %ISCC%
echo Membuat installer...
"%ISCC%" installer.iss
echo.
echo Selesai! Installer ada di folder installer_output\
pause
