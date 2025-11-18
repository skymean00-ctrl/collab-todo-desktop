@echo off
REM Collab Todo Desktop - C# / .NET 빌드 스크립트
REM 단일 .exe 파일을 생성합니다.

echo ========================================
echo Collab Todo Desktop - C# 빌드
echo ========================================
echo.

REM 프로젝트 디렉토리로 이동
cd /d "%~dp0"

echo [1/2] 프로젝트 빌드 중...
dotnet build -c Release
if errorlevel 1 (
    echo [오류] 빌드 실패
    pause
    exit /b 1
)

echo.
echo [2/2] 단일 실행 파일 생성 중...
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true
if errorlevel 1 (
    echo [오류] 배포 실패
    pause
    exit /b 1
)

echo.
echo ========================================
echo 빌드 완료!
echo ========================================
echo.
echo 실행 파일 위치:
echo   bin\Release\net8.0\win-x64\publish\CollabTodoDesktop.exe
echo.
echo 파일 정보:
dir "bin\Release\net8.0\win-x64\publish\CollabTodoDesktop.exe"
echo.
echo 이 파일을 사용자에게 배포하면 됩니다.
echo Python 설치가 필요 없습니다!
echo.
pause

