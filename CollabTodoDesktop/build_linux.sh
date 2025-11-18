#!/bin/bash
# ============================================================
# Collab Todo Desktop - C# / .NET 빌드 스크립트 (Linux)
# Linux에서 Windows용 실행 파일(.exe)을 생성합니다.
# ============================================================

set -e

echo ""
echo "============================================================"
echo "Collab Todo Desktop - C# / .NET 릴리스 빌드 (Linux)"
echo "============================================================"
echo ""

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# .NET SDK 확인
if ! command -v dotnet &> /dev/null; then
    echo "[오류] .NET SDK가 설치되어 있지 않습니다."
    echo ""
    echo ".NET 8.0 SDK를 설치하세요:"
    echo "  Ubuntu/Debian:"
    echo "    wget https://dot.net/v1/dotnet-install.sh"
    echo "    chmod +x dotnet-install.sh"
    echo "    ./dotnet-install.sh --channel 8.0"
    echo ""
    echo "  또는:"
    echo "    https://dotnet.microsoft.com/download/dotnet/8.0"
    echo ""
    exit 1
fi

echo "[1/3] .NET SDK 버전 확인..."
dotnet --version
echo ""

echo "[2/3] 프로젝트 빌드 중..."
dotnet build -c Release
if [ $? -ne 0 ]; then
    echo "[오류] 빌드 실패"
    exit 1
fi
echo ""

echo "[3/3] Windows용 단일 실행 파일 생성 중..."
echo "       (Self-contained, 모든 의존성 포함)"
echo ""

dotnet publish -c Release -r win-x64 --self-contained true \
    -p:PublishSingleFile=true \
    -p:IncludeNativeLibrariesForSelfExtract=true \
    -p:PublishReadyToRun=true

if [ $? -ne 0 ]; then
    echo "[오류] 배포 실패"
    exit 1
fi

echo ""
echo "============================================================"
echo "빌드 완료!"
echo "============================================================"
echo ""
echo "실행 파일 위치:"
echo "  bin/Release/net8.0/win-x64/publish/CollabTodoDesktop.exe"
echo ""

if [ -f "bin/Release/net8.0/win-x64/publish/CollabTodoDesktop.exe" ]; then
    echo "파일 정보:"
    ls -lh "bin/Release/net8.0/win-x64/publish/CollabTodoDesktop.exe"
    echo ""
    echo "이 파일을 Windows PC로 전송하여 사용할 수 있습니다."
    echo "Python 설치가 필요 없습니다!"
    echo ""
    echo "다음 단계:"
    echo "  1. bin/Release/net8.0/win-x64/publish/CollabTodoDesktop.exe 복사"
    echo "  2. Windows PC로 전송 (scp, USB, 네트워크 공유 등)"
    echo "  3. appsettings.json 파일 생성 (선택사항)"
    echo "  4. Windows에서 CollabTodoDesktop.exe 실행"
else
    echo "[오류] 실행 파일을 찾을 수 없습니다."
    echo "빌드 출력 디렉토리를 확인하세요."
fi

echo ""

