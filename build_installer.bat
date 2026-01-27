@echo off
REM ===========================================================
REM  KIAS Dørkonfigurator - Bygg installasjonsprogram
REM  Kjør fra prosjektroten.
REM ===========================================================
setlocal

echo ============================================
echo  KIAS Dorkonfigurator - Bygg installer
echo ============================================
echo.

REM --- Steg 1: Rens tidligere bygg ---
echo [1/4] Renser tidligere bygg...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
echo       Ferdig.
echo.

REM --- Steg 2: Installer avhengigheter ---
echo [2/4] Installerer avhengigheter med uv...
uv sync
if errorlevel 1 (
    echo FEIL: uv sync feilet!
    exit /b 1
)
echo       Ferdig.
echo.

REM --- Steg 3: Bygg med PyInstaller ---
echo [3/4] Bygger applikasjon med PyInstaller...
uv run pyinstaller kias_dorkonfigurator.spec --noconfirm
if errorlevel 1 (
    echo FEIL: PyInstaller-bygg feilet!
    exit /b 1
)
echo       Ferdig.
echo.

REM --- Steg 4: Bygg installer med Inno Setup ---
echo [4/4] Bygger installer med Inno Setup...

set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if "%ISCC%"=="" (
    echo ADVARSEL: Inno Setup ikke funnet!
    echo Last ned fra: https://jrsoftware.org/isdl.php
    echo PyInstaller-bygget er tilgjengelig i dist\
    exit /b 1
)

"%ISCC%" installer\kias_installer.iss
if errorlevel 1 (
    echo FEIL: Inno Setup-bygg feilet!
    exit /b 1
)
echo       Ferdig.
echo.

echo ============================================
echo  BYGG FULLFORT!
echo  Installer: installer\Output\
echo ============================================
endlocal
