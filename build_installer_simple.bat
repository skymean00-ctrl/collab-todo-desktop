@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Collab Todo Desktop 설치 프로그램 빌드
echo ========================================
echo.

REM 현재 디렉토리 확인
cd /d "%~dp0"
echo 작업 디렉토리: %CD%
echo.

REM 1단계: Python 확인
echo [1/4] Python 확인 중...
python --version
if errorlevel 1 (
    echo [오류] Python을 찾을 수 없습니다.
    echo Python 3.11 이상을 설치하세요.
    pause
    exit /b 1
)
echo.

REM 2단계: 가상환경 활성화
echo [2/4] 가상환경 활성화 중...
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo 가상환경이 없습니다. 생성 중...
    python -m venv .venv
    if errorlevel 1 (
        echo [오류] 가상환경 생성 실패
        pause
        exit /b 1
    )
    call ".venv\Scripts\activate.bat"
)
echo.

REM 3단계: PyInstaller 빌드
echo [3/4] PyInstaller로 실행 파일 빌드 중...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

pyinstaller pyinstaller.spec --clean --noconfirm
if errorlevel 1 (
    echo [오류] PyInstaller 빌드 실패
    pause
    exit /b 1
)

if not exist "dist\CollabToDoDesktop.exe" (
    echo [오류] 실행 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)
echo 빌드 완료: dist\CollabToDoDesktop.exe
echo.

REM 4단계: Inno Setup 컴파일
echo [4/4] Inno Setup으로 설치 프로그램 생성 중...

set "INNO_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if "!INNO_PATH!"=="" (
    echo [오류] Inno Setup을 찾을 수 없습니다.
    echo.
    echo Inno Setup 6을 설치하세요: https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

echo Inno Setup 경로: !INNO_PATH!
"%INNO_PATH%" "%~dp0installer.iss"
if errorlevel 1 (
    echo [오류] 설치 프로그램 생성 실패
    pause
    exit /b 1
)

echo.
echo ========================================
echo 빌드 완료!
echo ========================================
if exist "installer\CollabTodoDesktop-Setup-1.0.0.exe" (
    echo.
    echo 설치 프로그램 위치:
    echo   installer\CollabTodoDesktop-Setup-1.0.0.exe
    echo.
    dir "installer\CollabTodoDesktop-Setup-1.0.0.exe"
) else (
    echo [오류] 설치 프로그램 파일을 찾을 수 없습니다.
)
echo.
pause

