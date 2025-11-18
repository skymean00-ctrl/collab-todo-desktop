@echo off
REM Windows 설치 프로그램 빌드 스크립트
REM 이 스크립트는 PyInstaller로 실행 파일을 빌드한 후 Inno Setup으로 설치 프로그램을 생성합니다.

setlocal enabledelayedexpansion

echo ========================================
echo Collab Todo Desktop 설치 프로그램 빌드
echo ========================================
echo.

REM Python 가상환경 활성화 확인
if exist ".venv\Scripts\activate.bat" (
    echo [1/4] 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
) else (
    echo 경고: 가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다.
)

REM PyInstaller로 실행 파일 빌드
echo [2/4] PyInstaller로 실행 파일 빌드 중...
pyinstaller pyinstaller.spec --clean --noconfirm
if errorlevel 1 (
    echo 오류: PyInstaller 빌드 실패
    pause
    exit /b 1
)

REM dist 디렉토리 확인
if not exist "dist\CollabToDoDesktop.exe" (
    echo 오류: 빌드된 실행 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)

echo [3/4] 빌드 완료: dist\CollabToDoDesktop.exe

REM Inno Setup 컴파일러 경로 확인
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_SETUP% (
    set INNO_SETUP="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist %INNO_SETUP% (
    echo.
    echo 오류: Inno Setup을 찾을 수 없습니다.
    echo 다음 경로 중 하나에 설치되어 있어야 합니다:
    echo   - C:\Program Files (x86)\Inno Setup 6\ISCC.exe
    echo   - C:\Program Files\Inno Setup 6\ISCC.exe
    echo.
    echo Inno Setup 다운로드: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

REM 설치 프로그램 생성
echo [4/4] Inno Setup으로 설치 프로그램 생성 중...
%INNO_SETUP% installer.iss
if errorlevel 1 (
    echo 오류: 설치 프로그램 생성 실패
    pause
    exit /b 1
)

echo.
echo ========================================
echo 빌드 완료!
echo ========================================
echo 설치 프로그램 위치: installer\CollabTodoDesktop-Setup-1.0.0.exe
echo.

pause

