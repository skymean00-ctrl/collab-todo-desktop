-- ============================================================
-- Collab Todo - v1 → v2 마이그레이션
-- 기존 데이터베이스에 신규 테이블/컬럼/인덱스만 추가합니다.
-- 적용 방법:
--   mysql -u root -p collab_todo < sql/migrate_v2.sql
-- ============================================================

USE collab_todo;

-- 1. refresh_tokens 테이블
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    token      VARCHAR(128) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    revoked    BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX ix_refresh_tokens_token   (token),
    INDEX ix_refresh_tokens_user_id (user_id)
);

-- 2. user_notification_preferences 테이블
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    user_id               INT PRIMARY KEY,
    notify_assigned       BOOLEAN DEFAULT TRUE,
    notify_status_changed BOOLEAN DEFAULT TRUE,
    notify_due_soon       BOOLEAN DEFAULT TRUE,
    notify_mentioned      BOOLEAN DEFAULT TRUE,
    notify_reassigned     BOOLEAN DEFAULT TRUE,
    notify_commented      BOOLEAN DEFAULT TRUE,
    email_assigned        BOOLEAN DEFAULT TRUE,
    email_status_changed  BOOLEAN DEFAULT TRUE,
    email_due_soon        BOOLEAN DEFAULT TRUE,
    email_mentioned       BOOLEAN DEFAULT TRUE,
    email_reassigned      BOOLEAN DEFAULT TRUE,
    updated_at            DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. filter_presets 테이블
CREATE TABLE IF NOT EXISTS filter_presets (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    name          VARCHAR(100) NOT NULL,
    section       VARCHAR(50),
    status        VARCHAR(50),
    priority      VARCHAR(50),
    sort_by       VARCHAR(50),
    sort_dir      VARCHAR(10),
    due_date_from DATE,
    due_date_to   DATE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX ix_filter_presets_user_id (user_id)
);

-- 4. system_settings 테이블
CREATE TABLE IF NOT EXISTS system_settings (
    `key`       VARCHAR(100) PRIMARY KEY,
    value       TEXT NOT NULL,
    description TEXT,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 5. task_favorites 테이블
CREATE TABLE IF NOT EXISTS task_favorites (
    user_id    INT NOT NULL,
    task_id    INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, task_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- 6. mentions 테이블
CREATE TABLE IF NOT EXISTS mentions (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    log_id            INT NOT NULL,
    mentioned_user_id INT NOT NULL,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (log_id)            REFERENCES task_logs(id) ON DELETE CASCADE,
    FOREIGN KEY (mentioned_user_id) REFERENCES users(id)     ON DELETE CASCADE,
    INDEX ix_mentions_log_id            (log_id),
    INDEX ix_mentions_mentioned_user_id (mentioned_user_id)
);

-- 7. password_reset_tokens 테이블 (v1에 없을 경우)
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    token      VARCHAR(64) NOT NULL UNIQUE,
    used       BOOLEAN DEFAULT FALSE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX ix_password_reset_tokens_token (token)
);

-- 8. tasks 테이블에 인덱스 추가 (중복 무시)
-- (이미 있으면 ALTER TABLE은 에러가 나므로 PROCEDURE로 안전하게 처리)
DROP PROCEDURE IF EXISTS add_index_if_not_exists;
DELIMITER $$
CREATE PROCEDURE add_index_if_not_exists(
    IN tbl VARCHAR(100),
    IN idx VARCHAR(100),
    IN col VARCHAR(200)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = tbl
          AND INDEX_NAME   = idx
    ) THEN
        SET @sql = CONCAT('ALTER TABLE ', tbl, ' ADD INDEX ', idx, ' (', col, ')');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$
DELIMITER ;

CALL add_index_if_not_exists('tasks', 'ix_tasks_assignee_status', 'assignee_id, status');
CALL add_index_if_not_exists('tasks', 'ix_tasks_assigner_status', 'assigner_id, status');
CALL add_index_if_not_exists('tasks', 'ix_tasks_due_date_status', 'due_date, status');
CALL add_index_if_not_exists('notifications', 'ix_notifications_is_read', 'is_read');
CALL add_index_if_not_exists('task_logs', 'ix_task_logs_task_id', 'task_id');

DROP PROCEDURE IF EXISTS add_index_if_not_exists;

-- 9. 기본 부서 삽입 (없으면)
INSERT IGNORE INTO departments (name) VALUES
    ('현장소장'), ('공무팀'), ('공사팀'), ('안전팀'), ('품질팀'), ('직영팀');

-- 10. 시스템 설정 기본값
INSERT IGNORE INTO system_settings (`key`, value, description) VALUES
    ('access_token_expire_minutes', '60',   'Access JWT 만료 시간 (분)'),
    ('refresh_token_expire_days',   '7',    'Refresh Token 만료 일수'),
    ('max_upload_size_mb',          '10',   '파일 업로드 최대 크기 (MB)'),
    ('allowed_file_types',          'pdf,docx,xlsx,pptx,jpg,jpeg,png,gif,zip,hwp',
                                            '허용 파일 확장자 (쉼표 구분)'),
    ('max_refresh_tokens_per_user', '5',    '사용자 당 최대 Refresh Token 수'),
    ('rate_limit_per_minute',       '200',  '분당 API 요청 제한'),
    ('due_soon_days_warning',       '3',    '마감 임박 경고 일수'),
    ('max_filter_presets',          '10',   '사용자 당 최대 필터 프리셋 수'),
    ('app_name',                    'CollabTodo', '서비스 이름'),
    ('app_version',                 '2.0.0', '현재 버전');

SELECT 'v2 마이그레이션 완료' AS status;
