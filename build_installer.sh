#!/bin/bash
# Windows 설치 프로그램 빌드 스크립트 (Linux/macOS에서 WINE 사용)
# 주의: 이 스크립트는 WINE 환경에서 Inno Setup을 실행합니다.

set -e

echo "========================================"
echo "Collab Todo Desktop 설치 프로그램 빌드"
echo "========================================"
echo ""

# Python 가상환경 활성화
if [ -f ".venv/bin/activate" ]; then
    echo "[1/5] 가상환경 활성화 중..."
    source .venv/bin/activate
else
    echo "경고: 가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다."
fi

# PyInstaller로 실행 파일 빌드
echo "[2/5] PyInstaller로 실행 파일 빌드 중..."
pyinstaller pyinstaller.spec --clean --noconfirm

# dist 디렉토리 확인
if [ ! -f "dist/CollabToDoDesktop.exe" ]; then
    echo "오류: 빌드된 실행 파일을 찾을 수 없습니다."
    exit 1
fi

echo "[3/5] 빌드 완료: dist/CollabToDoDesktop.exe"

# WINE 및 Inno Setup 확인
if ! command -v wine &> /dev/null; then
    echo ""
    echo "오류: WINE이 설치되어 있지 않습니다."
    echo "WINE 설치가 필요합니다 (Inno Setup을 Windows 환경에서 실행하기 위해)."
    echo ""
    echo "대안: Windows 환경에서 build_installer.bat를 실행하세요."
    exit 1
fi

# Inno Setup 설치 확인
INNO_SETUP_PATH="$HOME/.wine/drive_c/Program Files (x86)/Inno Setup 6/ISCC.exe"
if [ ! -f "$INNO_SETUP_PATH" ]; then
    INNO_SETUP_PATH="$HOME/.wine/drive_c/Program Files/Inno Setup 6/ISCC.exe"
fi

if [ ! -f "$INNO_SETUP_PATH" ]; then
    echo ""
    echo "오류: Inno Setup을 찾을 수 없습니다."
    echo "WINE 환경에 Inno Setup을 설치해야 합니다."
    echo ""
    echo "설치 방법:"
    echo "1. https://jrsoftware.org/isdl.php 에서 Inno Setup 다운로드"
    echo "2. wine inno-setup-installer.exe 로 설치"
    echo ""
    echo "또는 Windows 환경에서 build_installer.bat를 실행하세요."
    exit 1
fi

# 설치 프로그램 생성
echo "[4/5] Inno Setup으로 설치 프로그램 생성 중..."
wine "$INNO_SETUP_PATH" installer.iss

if [ $? -ne 0 ]; then
    echo "오류: 설치 프로그램 생성 실패"
    exit 1
fi

echo ""
echo "========================================"
echo "빌드 완료!"
echo "========================================"
echo "설치 프로그램 위치: installer/CollabTodoDesktop-Setup-1.0.0.exe"
echo ""

