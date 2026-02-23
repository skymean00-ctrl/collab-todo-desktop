#!/bin/bash
set -euo pipefail

# 웹 원격 환경에서만 실행
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

echo "=== [session-start] 프론트엔드 의존성 설치 (npm) ==="
cd "$PROJECT_DIR/frontend"
npm install

echo "=== [session-start] 백엔드 의존성 설치 (pip) ==="
cd "$PROJECT_DIR/backend"
pip install -r requirements.txt --quiet

echo "=== [session-start] 완료 ==="
