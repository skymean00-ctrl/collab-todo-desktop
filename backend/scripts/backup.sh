#!/usr/bin/env bash
# ============================================================
# Collab Todo - DB 백업 스크립트
# ============================================================
# 사용법:
#   chmod +x backend/scripts/backup.sh
#   ./backend/scripts/backup.sh
#
# 환경변수 (.env 파일 또는 export로 설정):
#   DB_HOST     (기본: localhost)
#   DB_PORT     (기본: 3306)
#   DB_USER     (기본: root)
#   DB_PASSWORD (기본: "")
#   DB_NAME     (기본: collab_todo)
#   BACKUP_DIR  (기본: ./backups)
#   KEEP_DAYS   보관 일수 (기본: 30)
#
# cron 등록 예시 (매일 새벽 2시):
#   0 2 * * * /path/to/collab-todo-desktop/backend/scripts/backup.sh >> /var/log/collab_backup.log 2>&1
# ============================================================

set -euo pipefail

# ── 설정 ────────────────────────────────────────────────────
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_NAME="${DB_NAME:-collab_todo}"
BACKUP_DIR="${BACKUP_DIR:-$(dirname "$0")/../../backups}"
KEEP_DAYS="${KEEP_DAYS:-30}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

# ── 백업 디렉토리 생성 ───────────────────────────────────────
mkdir -p "${BACKUP_DIR}"

# ── 백업 실행 ────────────────────────────────────────────────
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 백업 시작: ${DB_NAME}"

if [ -n "${DB_PASSWORD}" ]; then
    MYSQL_PWD="${DB_PASSWORD}" mysqldump \
        -h "${DB_HOST}" \
        -P "${DB_PORT}" \
        -u "${DB_USER}" \
        --single-transaction \
        --routines \
        --triggers \
        --add-drop-table \
        --default-character-set=utf8mb4 \
        "${DB_NAME}" | gzip > "${BACKUP_FILE}"
else
    mysqldump \
        -h "${DB_HOST}" \
        -P "${DB_PORT}" \
        -u "${DB_USER}" \
        --single-transaction \
        --routines \
        --triggers \
        --add-drop-table \
        --default-character-set=utf8mb4 \
        "${DB_NAME}" | gzip > "${BACKUP_FILE}"
fi

BACKUP_SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 백업 완료: ${BACKUP_FILE} (${BACKUP_SIZE})"

# ── 오래된 백업 정리 ─────────────────────────────────────────
DELETED=$(find "${BACKUP_DIR}" -name "${DB_NAME}_*.sql.gz" -mtime "+${KEEP_DAYS}" -print -delete | wc -l)
if [ "${DELETED}" -gt 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 오래된 백업 ${DELETED}개 삭제 (보관 기간: ${KEEP_DAYS}일)"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 현재 백업 파일 목록:"
ls -lh "${BACKUP_DIR}/${DB_NAME}_"*.sql.gz 2>/dev/null || echo "  (없음)"
