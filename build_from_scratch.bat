@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM ============================================================
REM Collab Todo Desktop - 원격에서 자동 다운로드 및 빌드 스크립트
REM 이 스크립트는 GitHub에서 프로젝트를 다운로드하고 빌드합니다.
REM ============================================================

echo.
echo ============================================================
echo Collab Todo Desktop - 자동 다운로드 및 빌드
echo ============================================================
echo.
echo 이 스크립트는 다음을 수행합니다:
echo   1. GitHub에서 프로젝트 다운로드
echo   2. Python 가상환경 생성
echo   3. 의존성 설치
echo   4. 실행 파일 빌드
echo   5. 설치 프로그램 생성
echo.
echo 인터넷 연결이 필요합니다.
echo.
pause

REM 현재 스크립트 위치 기준으로 작업 디렉토리 설정
set "SCRIPT_DIR=%~dp0"
set "CURRENT_DIR=%CD%"
set "PROJECT_DIR=%CURRENT_DIR%\collab-todo-desktop"

REM GitHub 저장소 URL
set "GITHUB_REPO=https://github.com/skymean00-ctrl/collab-todo-desktop.git"
set "GITHUB_ZIP=https://github.com/skymean00-ctrl/collab-todo-desktop/archive/refs/heads/main.zip"

REM ============================================================
REM 1단계: 환경 확인
REM ============================================================
echo.
echo [1/6] 환경 확인 중...
echo.

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo.
    echo Python 3.11 이상을 설치하세요:
    echo   https://www.python.org/downloads/
    echo.
    echo 설치 시 "Add Python to PATH" 옵션을 체크하세요.
    echo.
    pause
    exit /b 1
)

python --version
echo.

REM Git 확인 (선택적)
git --version >nul 2>&1
set "HAS_GIT=0"
if not errorlevel 1 (
    set "HAS_GIT=1"
    echo Git이 설치되어 있습니다. (Git 사용)
) else (
    echo Git이 없습니다. ZIP 다운로드를 사용합니다.
)
echo.

REM ============================================================
REM 2단계: 프로젝트 다운로드
REM ============================================================
echo [2/6] 프로젝트 다운로드 중...
echo.

REM 기존 프로젝트 디렉토리가 있으면 삭제
if exist "%PROJECT_DIR%" (
    echo 기존 프로젝트 폴더를 삭제합니다...
    rmdir /s /q "%PROJECT_DIR%" 2>nul
)

REM Git이 있으면 clone, 없으면 ZIP 다운로드
if "!HAS_GIT!"=="1" (
    echo Git을 사용하여 프로젝트를 다운로드합니다...
    git clone %GITHUB_REPO% "%PROJECT_DIR%"
    if errorlevel 1 (
        echo [경고] Git clone 실패. ZIP 다운로드를 시도합니다...
        set "HAS_GIT=0"
    ) else (
        echo [완료] Git clone 성공
        goto :build_start
    )
)

if "!HAS_GIT!"=="0" (
    echo ZIP 파일을 다운로드합니다...
    
    REM PowerShell을 사용하여 ZIP 다운로드
    set "ZIP_FILE=%CURRENT_DIR%\project.zip"
    
    echo PowerShell로 다운로드 중...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ProgressPreference = 'SilentlyContinue'; ^
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
        try { ^
            Invoke-WebRequest -Uri '%GITHUB_ZIP%' -OutFile '%ZIP_FILE%' -UseBasicParsing; ^
            Write-Host '다운로드 완료' ^
        } catch { ^
            Write-Host '다운로드 실패:' $_.Exception.Message; ^
            exit 1 ^
        }"
    
    if not exist "%ZIP_FILE%" (
        echo [오류] 프로젝트 다운로드 실패
        echo.
        echo 수동 다운로드 방법:
        echo   1. 브라우저에서 다음 URL 열기:
        echo      %GITHUB_ZIP%
        echo   2. ZIP 파일을 현재 폴더에 저장
        echo   3. 파일 이름을 project.zip으로 변경
        echo   4. 이 스크립트를 다시 실행
        echo.
        pause
        exit /b 1
    )
    
    REM ZIP 압축 해제
    echo ZIP 파일 압축 해제 중...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "try { ^
            Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%CURRENT_DIR%' -Force; ^
            Write-Host '압축 해제 완료' ^
        } catch { ^
            Write-Host '압축 해제 실패:' $_.Exception.Message; ^
            exit 1 ^
        }"
    
    if errorlevel 1 (
        echo [오류] ZIP 압축 해제 실패
        pause
        exit /b 1
    )
    
    REM 압축 해제된 폴더 이름 확인 및 변경
    if exist "%CURRENT_DIR%\collab-todo-desktop-main" (
        move "%CURRENT_DIR%\collab-todo-desktop-main" "%PROJECT_DIR%" >nul 2>&1
    )
    
    REM ZIP 파일 삭제
    del "%ZIP_FILE%" >nul 2>&1
)

:build_start
if not exist "%PROJECT_DIR%" (
    echo [오류] 프로젝트 폴더를 찾을 수 없습니다.
    pause
    exit /b 1
)

echo [완료] 프로젝트 다운로드 완료
echo.

REM 프로젝트 디렉토리로 이동
cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo [오류] 프로젝트 디렉토리로 이동 실패
    pause
    exit /b 1
)

REM ============================================================
REM 3단계: 가상환경 생성
REM ============================================================
echo [3/6] 가상환경 생성 중...
echo.

if not exist ".venv\Scripts\activate.bat" (
    python -m venv ".venv"
    if errorlevel 1 (
        echo [오류] 가상환경 생성 실패
        pause
        exit /b 1
    )
)
echo [완료] 가상환경 생성 완료
echo.

REM ============================================================
REM 4단계: 의존성 설치
REM ============================================================
echo [4/6] 의존성 설치 중...
echo.

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [오류] 가상환경 활성화 실패
    pause
    exit /b 1
)

pip install --upgrade pip >nul 2>&1
echo pip 업그레이드 완료
pip install -r requirements.txt
if errorlevel 1 (
    echo [오류] 의존성 설치 실패
    pause
    exit /b 1
)
echo [완료] 의존성 설치 완료
echo.

REM ============================================================
REM 5단계: 실행 파일 빌드
REM ============================================================
echo [5/6] PyInstaller로 실행 파일 빌드 중...
echo.

if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul

pyinstaller pyinstaller.spec --clean --noconfirm
if errorlevel 1 (
    echo [오류] PyInstaller 빌드 실패
    pause
    exit /b 1
)

if not exist "dist\CollabToDoDesktop.exe" (
    echo [오류] 실행 파일을 찾을 수 없습니다.
    echo dist 디렉토리 내용:
    dir dist 2>nul
    pause
    exit /b 1
)
echo [완료] 실행 파일 빌드 완료: dist\CollabToDoDesktop.exe
echo.

REM ============================================================
REM 6단계: 설치 프로그램 생성
REM ============================================================
echo [6/6] Inno Setup으로 설치 프로그램 생성 중...
echo.

REM Inno Setup 경로 확인
set "INNO_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if "!INNO_PATH!"=="" (
    echo [경고] Inno Setup을 찾을 수 없습니다.
    echo.
    echo Inno Setup 6을 설치하세요: https://jrsoftware.org/isdl.php
    echo.
    echo 설치 후 이 스크립트를 다시 실행하거나,
    echo dist\CollabToDoDesktop.exe 파일을 직접 사용할 수 있습니다.
    echo.
    echo 실행 파일 위치: %PROJECT_DIR%\dist\CollabToDoDesktop.exe
    echo.
    pause
    exit /b 0
)

echo Inno Setup 경로: !INNO_PATH!
"!INNO_PATH!" "%~dp0installer.iss"
if errorlevel 1 (
    echo [오류] 설치 프로그램 생성 실패
    pause
    exit /b 1
)

REM ============================================================
REM 완료
REM ============================================================
echo.
echo ============================================================
echo 빌드 완료!
echo ============================================================
echo.

if exist "installer\CollabTodoDesktop-Setup-1.0.0.exe" (
    echo 설치 프로그램 위치:
    echo   %PROJECT_DIR%\installer\CollabTodoDesktop-Setup-1.0.0.exe
    echo.
    echo 이 파일을 사용자에게 배포하면 됩니다.
    echo.
    echo 파일 정보:
    dir "installer\CollabTodoDesktop-Setup-1.0.0.exe" | findstr "CollabTodoDesktop-Setup"
) else (
    echo [경고] 설치 프로그램 파일을 찾을 수 없습니다.
    echo 실행 파일은 다음 위치에 있습니다:
    echo   %PROJECT_DIR%\dist\CollabToDoDesktop.exe
    echo.
    echo 이 파일도 배포 가능합니다.
)

echo.
pause
