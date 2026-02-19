#!/bin/bash
# ============================================================
# Collab Todo Desktop - 배포 스크립트
# 사용법: 서버에서 직접 실행
#   ./scripts/deploy.sh              # 기본 배포 (pull + 의존성 + 마이그레이션)
#   ./scripts/deploy.sh --skip-migrate  # 마이그레이션 건너뛰기
#   ./scripts/deploy.sh --only-pull     # git pull만 실행
# ============================================================

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 프로젝트 루트 결정
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"
LOG_FILE="$PROJECT_DIR/deploy.log"

# 옵션 파싱
SKIP_MIGRATE=false
ONLY_PULL=false
for arg in "$@"; do
    case $arg in
        --skip-migrate) SKIP_MIGRATE=true ;;
        --only-pull)    ONLY_PULL=true ;;
        --help|-h)
            echo "사용법: deploy.sh [옵션]"
            echo "  --skip-migrate  DB 마이그레이션 건너뛰기"
            echo "  --only-pull     git pull만 실행"
            echo "  --help, -h      이 도움말 표시"
            exit 0
            ;;
    esac
done

# 로그 함수
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${BLUE}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

success() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] OK: $1"
    echo -e "${GREEN}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

warn() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $1"
    echo -e "${YELLOW}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
}

fail() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1"
    echo -e "${RED}${msg}${NC}"
    echo "$msg" >> "$LOG_FILE"
    exit 1
}

# .env 파일 로드
load_env() {
    if [ -f "$ENV_FILE" ]; then
        set -a
        # shellcheck disable=SC1090
        source "$ENV_FILE"
        set +a
        log ".env 파일 로드 완료"
    else
        warn ".env 파일 없음 ($ENV_FILE). 환경 변수가 직접 설정되어 있어야 합니다."
    fi
}

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE} Collab Todo Desktop - 배포 시작${NC}"
echo -e "${BLUE} $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

cd "$PROJECT_DIR"
load_env

BRANCH="${DEPLOY_BRANCH:-main}"

# ============================================================
# 1단계: Git Pull
# ============================================================
log "[1/4] 최신 코드 가져오는 중... (branch: $BRANCH)"

# 현재 변경사항 확인
if [ -n "$(git status --porcelain)" ]; then
    warn "로컬에 변경사항이 있습니다. stash 처리합니다."
    git stash push -m "deploy-auto-stash-$(date +%s)"
fi

BEFORE_HASH=$(git rev-parse HEAD)
git fetch origin "$BRANCH"
git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" "origin/$BRANCH"
git pull origin "$BRANCH"
AFTER_HASH=$(git rev-parse HEAD)

if [ "$BEFORE_HASH" = "$AFTER_HASH" ]; then
    success "이미 최신 상태입니다. ($BEFORE_HASH)"
else
    success "업데이트 완료: ${BEFORE_HASH:0:8} -> ${AFTER_HASH:0:8}"
    # 변경된 파일 목록 표시
    echo "  변경된 파일:"
    git diff --name-only "$BEFORE_HASH" "$AFTER_HASH" | sed 's/^/    /'
fi

if [ "$ONLY_PULL" = true ]; then
    success "git pull 완료 (--only-pull 모드)"
    exit 0
fi

# ============================================================
# 2단계: Python 의존성 업데이트
# ============================================================
log "[2/4] Python 의존성 확인..."

if [ -d "$PROJECT_DIR/venv" ]; then
    PIP="$PROJECT_DIR/venv/bin/pip"
else
    PIP="pip3"
    warn "가상환경 없음. 시스템 pip 사용"
fi

# requirements.txt 변경 확인
if git diff "$BEFORE_HASH" "$AFTER_HASH" --name-only | grep -q "requirements.txt"; then
    log "requirements.txt 변경 감지 - 의존성 업데이트 중..."
    $PIP install --quiet -r requirements.txt
    success "의존성 업데이트 완료"
else
    success "의존성 변경 없음 (건너뜀)"
fi

# ============================================================
# 3단계: SQL 마이그레이션 실행
# ============================================================
if [ "$SKIP_MIGRATE" = true ]; then
    warn "[3/4] 마이그레이션 건너뜀 (--skip-migrate)"
else
    log "[3/4] SQL 마이그레이션 확인..."

    # 새로운 SQL 파일 확인
    NEW_SQL_FILES=$(git diff "$BEFORE_HASH" "$AFTER_HASH" --name-only --diff-filter=A -- 'sql/*.sql' 2>/dev/null || true)

    if [ -n "$NEW_SQL_FILES" ]; then
        log "새 SQL 마이그레이션 파일 감지:"
        echo "$NEW_SQL_FILES" | sed 's/^/    /'

        # DB 연결 정보 확인
        DB_HOST="${COLLAB_TODO_DB_HOST:-}"
        DB_PORT="${COLLAB_TODO_DB_PORT:-3306}"
        DB_USER="${COLLAB_TODO_DB_USER:-}"
        DB_PASS="${COLLAB_TODO_DB_PASSWORD:-}"
        DB_NAME="${COLLAB_TODO_DB_NAME:-}"

        if [ -n "$DB_HOST" ] && [ -n "$DB_USER" ] && [ -n "$DB_NAME" ]; then
            for sql_file in $NEW_SQL_FILES; do
                log "  실행 중: $sql_file"
                if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$sql_file" 2>/dev/null; then
                    success "  $sql_file 실행 완료"
                else
                    warn "  $sql_file 실행 실패 (이미 적용되었거나 오류 발생)"
                fi
            done
        else
            warn "DB 연결 정보가 설정되지 않아 마이그레이션을 건너뜁니다."
            warn "수동으로 실행하세요: mysql -u <USER> -p <DB> < sql/<file>.sql"
        fi
    else
        success "새 마이그레이션 없음 (건너뜀)"
    fi
fi

# ============================================================
# 4단계: 테스트 실행
# ============================================================
log "[4/4] 테스트 실행..."

if [ -d "$PROJECT_DIR/venv" ]; then
    PYTHON="$PROJECT_DIR/venv/bin/python"
    PYTEST="$PROJECT_DIR/venv/bin/pytest"
else
    PYTHON="python3"
    PYTEST="pytest"
fi

if [ -f "$PYTEST" ] || command -v pytest &>/dev/null; then
    if $PYTEST "$PROJECT_DIR/tests/" -q --tb=short 2>/dev/null; then
        success "테스트 통과"
    else
        warn "일부 테스트 실패. 배포는 계속 진행됩니다."
    fi
else
    warn "pytest를 찾을 수 없어 테스트를 건너뜁니다."
fi

# ============================================================
# 완료
# ============================================================
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN} 배포 완료! $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${GREEN} 커밋: $(git rev-parse --short HEAD)${NC}"
echo -e "${GREEN} 브랜치: $(git branch --show-current)${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "로그 파일: $LOG_FILE"
