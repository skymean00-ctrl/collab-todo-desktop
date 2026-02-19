#!/bin/bash
# ============================================================
# Collab Todo Desktop - Ubuntu 서버 초기 설정 스크립트
# 사용법: ssh 접속 후 한 번만 실행
#   chmod +x server_setup.sh && sudo ./server_setup.sh
# ============================================================

set -euo pipefail

APP_USER="${APP_USER:-collabtodo}"
APP_DIR="/opt/collab-todo-desktop"
REPO_URL="${REPO_URL:-https://github.com/skymean00-ctrl/collab-todo-desktop.git}"
BRANCH="${BRANCH:-main}"

echo "============================================"
echo " Collab Todo Desktop - 서버 초기 설정"
echo "============================================"

# ------------------------------------------------------------
# 1. 시스템 패키지 업데이트 및 필수 패키지 설치
# ------------------------------------------------------------
echo "[1/6] 시스템 패키지 업데이트..."
apt-get update -qq
apt-get install -y -qq \
    git \
    python3 \
    python3-pip \
    python3-venv \
    mysql-client \
    curl \
    ufw

# ------------------------------------------------------------
# 2. 전용 사용자 생성 (이미 있으면 건너뜀)
# ------------------------------------------------------------
echo "[2/6] 애플리케이션 사용자 확인..."
if id "$APP_USER" &>/dev/null; then
    echo "  -> 사용자 '$APP_USER' 이미 존재"
else
    useradd -m -s /bin/bash "$APP_USER"
    echo "  -> 사용자 '$APP_USER' 생성 완료"
fi

# ------------------------------------------------------------
# 3. 프로젝트 디렉토리 생성 및 Git clone
# ------------------------------------------------------------
echo "[3/6] 프로젝트 디렉토리 설정..."
if [ -d "$APP_DIR/.git" ]; then
    echo "  -> 이미 clone되어 있음. git pull 실행..."
    cd "$APP_DIR"
    sudo -u "$APP_USER" git pull origin "$BRANCH"
else
    mkdir -p "$APP_DIR"
    git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR"
    chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
    echo "  -> clone 완료: $APP_DIR"
fi

# ------------------------------------------------------------
# 4. Python 가상환경 및 의존성 설치
# ------------------------------------------------------------
echo "[4/6] Python 가상환경 설정..."
cd "$APP_DIR"
if [ ! -d "venv" ]; then
    sudo -u "$APP_USER" python3 -m venv venv
fi
sudo -u "$APP_USER" venv/bin/pip install --quiet --upgrade pip
sudo -u "$APP_USER" venv/bin/pip install --quiet -r requirements.txt

echo "  -> Python 의존성 설치 완료"

# ------------------------------------------------------------
# 5. 환경 변수 템플릿 생성
# ------------------------------------------------------------
echo "[5/6] 환경 변수 파일 생성..."
ENV_FILE="$APP_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<'ENVEOF'
# ============================================================
# Collab Todo Desktop - 서버 환경 변수
# 이 파일을 실제 값으로 수정하세요
# ============================================================

# MySQL 데이터베이스 설정
COLLAB_TODO_DB_HOST=your-nas-ip-or-hostname
COLLAB_TODO_DB_PORT=3306
COLLAB_TODO_DB_USER=collab_todo_user
COLLAB_TODO_DB_PASSWORD=your-secure-password
COLLAB_TODO_DB_NAME=collab_todo
COLLAB_TODO_DB_USE_SSL=false

# AI 서비스 설정 (선택사항)
# COLLAB_TODO_AI_BASE_URL=http://localhost:11434
# COLLAB_TODO_AI_API_KEY=
# COLLAB_TODO_AI_TIMEOUT_SECONDS=15

# 배포 설정
DEPLOY_BRANCH=main
DEPLOY_RUN_MIGRATIONS=true
ENVEOF
    chown "$APP_USER":"$APP_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "  -> .env 템플릿 생성됨. 실제 값으로 수정 필요!"
    echo "     파일 위치: $ENV_FILE"
else
    echo "  -> .env 파일 이미 존재 (건너뜀)"
fi

# ------------------------------------------------------------
# 6. 배포 스크립트에 실행 권한 부여
# ------------------------------------------------------------
echo "[6/6] 배포 스크립트 권한 설정..."
if [ -f "$APP_DIR/scripts/deploy.sh" ]; then
    chmod +x "$APP_DIR/scripts/deploy.sh"
    echo "  -> deploy.sh 실행 권한 설정 완료"
fi

# ------------------------------------------------------------
# 완료 메시지
# ------------------------------------------------------------
echo ""
echo "============================================"
echo " 초기 설정 완료!"
echo "============================================"
echo ""
echo " 다음 단계:"
echo "  1. .env 파일을 실제 DB 정보로 수정하세요:"
echo "     sudo -u $APP_USER nano $ENV_FILE"
echo ""
echo "  2. DB 스키마 초기화 (처음인 경우):"
echo "     mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME> < $APP_DIR/sql/schema_mysql.sql"
echo ""
echo "  3. 배포 테스트:"
echo "     sudo -u $APP_USER $APP_DIR/scripts/deploy.sh"
echo ""
echo "  4. (선택) GitHub Actions 자동 배포를 위한 SSH 키 설정:"
echo "     sudo -u $APP_USER ssh-keygen -t ed25519 -C 'github-deploy'"
echo "     -> 생성된 공개키를 ~/.ssh/authorized_keys에 추가"
echo "     -> 개인키를 GitHub Secrets에 DEPLOY_SSH_KEY로 등록"
echo ""
