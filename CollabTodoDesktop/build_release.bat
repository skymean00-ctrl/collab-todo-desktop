@echo off
chcp 65001 >nul
REM ============================================================
REM Collab Todo Desktop - C# / .NET 릴리스 빌드 스크립트
REM 단일 실행 파일(.exe)을 생성합니다.
REM ============================================================

echo.
echo ============================================================
echo Collab Todo Desktop - C# / .NET 릴리스 빌드
echo ============================================================
echo.

REM 프로젝트 디렉토리로 이동
cd /d "%~dp0"

REM .NET SDK 확인
dotnet --version >nul 2>&1
if errorlevel 1 (
    echo [오류] .NET SDK가 설치되어 있지 않습니다.
    echo.
    echo .NET 8.0 SDK를 설치하세요:
    echo   https://dotnet.microsoft.com/download/dotnet/8.0
    echo.
    pause
    exit /b 1
)

echo [1/3] .NET SDK 버전 확인...
dotnet --version
echo.

echo [2/3] 프로젝트 빌드 중...
dotnet build -c Release
if errorlevel 1 (
    echo [오류] 빌드 실패
    pause
    exit /b 1
)
echo.

echo [3/3] 단일 실행 파일 생성 중...
echo        (Self-contained, 모든 의존성 포함)
echo.

dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:PublishReadyToRun=true
if errorlevel 1 (
    echo [오류] 배포 실패
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 빌드 완료!
echo ============================================================
echo.
echo 실행 파일 위치:
echo   bin\Release\net8.0\win-x64\publish\CollabTodoDesktop.exe
echo.
echo 파일 정보:
if exist "bin\Release\net8.0\win-x64\publish\CollabTodoDesktop.exe" (
    dir "bin\Release\net8.0\win-x64\publish\CollabTodoDesktop.exe"
    echo.
    echo 이 파일을 사용자에게 배포하면 됩니다.
    echo Python 설치가 필요 없습니다!
    echo.
    echo 다음 단계:
    echo   1. bin\Release\net8.0\win-x64\publish\CollabTodoDesktop.exe 복사
    echo   2. appsettings.json 파일 생성 (선택사항)
    echo   3. 실행 파일과 appsettings.json을 같은 폴더에 배치
    echo   4. CollabTodoDesktop.exe 실행
) else (
    echo [오류] 실행 파일을 찾을 수 없습니다.
    echo 빌드 출력 디렉토리를 확인하세요.
)

echo.
pause

