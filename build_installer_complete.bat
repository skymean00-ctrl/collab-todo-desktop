@echo off
chcp 65001 >nul
REM ============================================================
REM Collab Todo Desktop - 완전한 설치 프로그램 빌드 스크립트
REM 모든 의존성이 포함된 독립 실행형 Windows 설치 파일 생성
REM 사용자가 Python 등을 별도로 설치할 필요가 없습니다.
REM ============================================================

setlocal enabledelayedexpansion

REM 현재 디렉토리로 이동 (스크립트 위치 기준)
cd /d "%~dp0"

echo.
echo ============================================================
echo Collab Todo Desktop - 완전한 설치 프로그램 빌드
echo ============================================================
echo.
echo 이 스크립트는 다음을 수행합니다:
echo   1. PyInstaller로 실행 파일 빌드 (Python 런타임 포함)
echo   2. Inno Setup으로 설치 프로그램 생성
echo   3. 모든 의존성이 포함된 독립 실행형 설치 파일 생성
echo.
echo 결과: installer\CollabTodoDesktop-Setup-1.0.0.exe
echo   - Python 런타임 포함 (사용자 설치 불필요)
echo   - 모든 라이브러리 포함
echo   - 단일 설치 파일로 배포 가능
echo.
pause

REM ============================================================
REM 1단계: 환경 확인
REM ============================================================
echo.
echo [1/5] 환경 확인 중...
echo.

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo Python 3.11 이상을 설치하세요: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 가상환경 확인 및 생성
if not exist ".venv\Scripts\activate.bat" (
    echo 가상환경이 없습니다. 생성 중...
    python -m venv ".venv"
    if errorlevel 1 (
        echo [오류] 가상환경 생성 실패
        pause
        exit /b 1
    )
)

REM ============================================================
REM 2단계: 가상환경 활성화 및 의존성 설치
REM ============================================================
echo [2/5] 가상환경 활성화 및 의존성 설치 중...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [오류] 가상환경 활성화 실패
    pause
    exit /b 1
)

REM 의존성 설치
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [오류] 의존성 설치 실패
    pause
    exit /b 1
)

REM ============================================================
REM 3단계: PyInstaller로 실행 파일 빌드
REM ============================================================
echo.
echo [3/5] PyInstaller로 실행 파일 빌드 중...
echo       (Python 런타임 및 모든 의존성 포함)
echo.

REM 기존 빌드 정리
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM 실행 파일 빌드
pyinstaller pyinstaller.spec --clean --noconfirm
if errorlevel 1 (
    echo [오류] PyInstaller 빌드 실패
    pause
    exit /b 1
)

REM 빌드 결과 확인
if not exist "dist\CollabToDoDesktop.exe" (
    echo [오류] 빌드된 실행 파일을 찾을 수 없습니다.
    echo dist 디렉토리를 확인하세요.
    pause
    exit /b 1
)

echo [완료] 실행 파일 빌드 완료: dist\CollabToDoDesktop.exe
echo        파일 크기:
dir "dist\CollabToDoDesktop.exe" | findstr "CollabToDoDesktop.exe"

REM ============================================================
REM 4단계: Inno Setup으로 설치 프로그램 생성
REM ============================================================
echo.
echo [4/5] Inno Setup으로 설치 프로그램 생성 중...
echo.

REM Inno Setup 컴파일러 경로 확인
set "INNO_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if "!INNO_PATH!"=="" (
    echo [오류] Inno Setup을 찾을 수 없습니다.
    echo.
    echo Inno Setup 6을 설치하세요:
    echo   https://jrsoftware.org/isdl.php
    echo.
    echo 설치 경로:
    echo   - C:\Program Files (x86)\Inno Setup 6\
    echo   - 또는 C:\Program Files\Inno Setup 6\
    echo.
    pause
    exit /b 1
)

REM 설치 프로그램 생성
echo Inno Setup 컴파일러 실행 중: !INNO_PATH!
"!INNO_PATH!" "%~dp0installer.iss"
if errorlevel 1 (
    echo [오류] 설치 프로그램 생성 실패
    pause
    exit /b 1
)

REM ============================================================
REM 5단계: 결과 확인
REM ============================================================
echo.
echo [5/5] 빌드 결과 확인 중...
echo.

if exist "installer\CollabTodoDesktop-Setup-1.0.0.exe" (
    echo ============================================================
    echo 빌드 성공!
    echo ============================================================
    echo.
    echo 설치 프로그램 위치:
    echo   installer\CollabTodoDesktop-Setup-1.0.0.exe
    echo.
    echo 파일 정보:
    dir "installer\CollabTodoDesktop-Setup-1.0.0.exe" | findstr "CollabTodoDesktop-Setup"
    echo.
    echo 이 설치 파일은 다음을 포함합니다:
    echo   - Python 런타임 (사용자 설치 불필요)
    echo   - 모든 Python 라이브러리 (PyQt5, mysql-connector 등)
    echo   - 애플리케이션 실행 파일
    echo   - 시작 메뉴 바로가기
    echo   - 제거 프로그램
    echo.
    echo 배포 준비 완료!
    echo 이 파일을 사용자에게 배포하면 됩니다.
    echo.
) else (
    echo [오류] 설치 프로그램 파일을 찾을 수 없습니다.
    echo installer 디렉토리를 확인하세요.
)

echo.
pause

