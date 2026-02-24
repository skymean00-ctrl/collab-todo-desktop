#!/bin/bash
# CollabTodo 업데이트 배포 스크립트
# 사용법: bash deploy.sh [버전]
# 예시:  bash deploy.sh 1.0.1

set -e

FRONTEND_DIR="$(dirname "$0")/frontend"
UPDATES_DIR="$(dirname "$0")/updates"

# 버전 인수 처리
if [ -n "$1" ]; then
  echo "▶ 버전을 $1 로 변경합니다..."
  # package.json version 업데이트
  sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$1\"/" "$FRONTEND_DIR/package.json"
  echo "  → package.json version: $1"
fi

CURRENT_VERSION=$(grep '"version"' "$FRONTEND_DIR/package.json" | head -1 | sed 's/.*": "\(.*\)".*/\1/')
echo ""
echo "======================================"
echo "  CollabTodo 배포 v$CURRENT_VERSION"
echo "======================================"

# 1. 빌드 (Docker + wine)
echo ""
echo "▶ 앱 빌드 중..."
docker run --rm \
  -e CI=true \
  -v "$FRONTEND_DIR:/project" \
  -w /project \
  electronuserland/builder:wine \
  bash -c "npm install -g pnpm && CI=true CSC_IDENTITY_AUTO_DISCOVERY=false pnpm install && CSC_IDENTITY_AUTO_DISCOVERY=false pnpm run deploy" 2>&1 | \
  grep -E "✓|building|Setup|error|⨯" || true

# 2. 업데이트 파일 복사
echo ""
echo "▶ 업데이트 파일 배포 중..."
mkdir -p "$UPDATES_DIR"

# latest.yml (버전 정보 - electron-updater가 이 파일로 신버전 감지)
if [ -f "$FRONTEND_DIR/dist-electron/latest.yml" ]; then
  cp "$FRONTEND_DIR/dist-electron/latest.yml" "$UPDATES_DIR/"
  echo "  → latest.yml 복사 완료"
else
  echo "  ⚠ latest.yml 없음 - 빌드 실패 확인 필요"
  exit 1
fi

# .exe 설치 파일
cp "$FRONTEND_DIR/dist-electron/"*.exe "$UPDATES_DIR/" 2>/dev/null && \
  echo "  → .exe 복사 완료" || echo "  ⚠ .exe 없음"

# .blockmap (빠른 델타 업데이트용)
cp "$FRONTEND_DIR/dist-electron/"*.blockmap "$UPDATES_DIR/" 2>/dev/null && \
  echo "  → .blockmap 복사 완료" || true

# 3. 결과 확인
echo ""
echo "▶ 업데이트 서버 파일 목록:"
ls -lh "$UPDATES_DIR/"

echo ""
echo "======================================"
echo "  배포 완료! v$CURRENT_VERSION"
echo "  URL: https://api.skymeanai.com/updates/latest.yml"
echo "======================================"
