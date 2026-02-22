-- ============================================================
-- Collab Todo - MySQL Schema (v2)
-- ============================================================
-- 적용 방법:
--   mysql -u root -p < sql/schema.sql
-- 기존 DB에 신규 테이블만 추가할 때:
--   mysql -u root -p collab_todo < sql/migrate_v2.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS collab_todo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE collab_todo;

-- ============================================================
-- 부서
-- ============================================================
CREATE TABLE IF NOT EXISTS departments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 사용자
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name          VARCHAR(100) NOT NULL,
    department_id INT,
    job_title     VARCHAR(100),
    is_active     BOOLEAN DEFAULT TRUE,
    is_admin      BOOLEAN DEFAULT FALSE,
    is_verified   BOOLEAN DEFAULT FALSE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    INDEX ix_users_email (email)
);

-- ============================================================
-- 이메일 인증 토큰
-- ============================================================
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    token      VARCHAR(64) NOT NULL UNIQUE,
    used       BOOLEAN DEFAULT FALSE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX ix_email_verification_tokens_token (token)
);

-- ============================================================
-- 비밀번호 재설정 토큰
-- ============================================================
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

-- ============================================================
-- [NEW v2] Refresh 토큰 (Access Token 재발급용, 7일 유효)
-- ============================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    token      VARCHAR(128) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    revoked    BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX ix_refresh_tokens_token (token),
    INDEX ix_refresh_tokens_user_id (user_id)
);

-- ============================================================
-- [NEW v2] 사용자별 알림 수신 설정
-- ============================================================
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    user_id              INT PRIMARY KEY,
    -- 인앱 알림
    notify_assigned      BOOLEAN DEFAULT TRUE,
    notify_status_changed BOOLEAN DEFAULT TRUE,
    notify_due_soon      BOOLEAN DEFAULT TRUE,
    notify_mentioned     BOOLEAN DEFAULT TRUE,
    notify_reassigned    BOOLEAN DEFAULT TRUE,
    notify_commented     BOOLEAN DEFAULT TRUE,
    -- 이메일 알림
    email_assigned       BOOLEAN DEFAULT TRUE,
    email_status_changed BOOLEAN DEFAULT TRUE,
    email_due_soon       BOOLEAN DEFAULT TRUE,
    email_mentioned      BOOLEAN DEFAULT TRUE,
    email_reassigned     BOOLEAN DEFAULT TRUE,
    updated_at           DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- [NEW v2] 필터 프리셋 (사용자별 대시보드 필터 저장, 최대 10개)
-- ============================================================
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

-- ============================================================
-- [NEW v2] 시스템 전역 설정 (하드코딩 대체, 관리자 DB 관리)
-- ============================================================
CREATE TABLE IF NOT EXISTS system_settings (
    `key`        VARCHAR(100) PRIMARY KEY,
    value        TEXT NOT NULL,
    description  TEXT,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================================
-- 카테고리 (업무 분류)
-- ============================================================
CREATE TABLE IF NOT EXISTS categories (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7) DEFAULT '#6366f1'
);

-- ============================================================
-- 태그
-- ============================================================
CREATE TABLE IF NOT EXISTS tags (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- ============================================================
-- 업무
-- ============================================================
CREATE TABLE IF NOT EXISTS tasks (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    content         TEXT,
    assigner_id     INT NOT NULL,
    assignee_id     INT NOT NULL,
    category_id     INT,
    priority        ENUM('urgent','high','normal','low') DEFAULT 'normal',
    status          ENUM('pending','in_progress','review','approved','rejected') DEFAULT 'pending',
    progress        TINYINT DEFAULT 0,
    estimated_hours DECIMAL(5,2),
    due_date        DATE,
    parent_task_id  INT,
    is_subtask      BOOLEAN DEFAULT FALSE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (assigner_id)    REFERENCES users(id),
    FOREIGN KEY (assignee_id)    REFERENCES users(id),
    FOREIGN KEY (category_id)    REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    -- 개별 인덱스
    INDEX ix_tasks_assignee_id (assignee_id),
    INDEX ix_tasks_assigner_id (assigner_id),
    INDEX ix_tasks_priority    (priority),
    INDEX ix_tasks_status      (status),
    INDEX ix_tasks_due_date    (due_date),
    INDEX ix_tasks_is_subtask  (is_subtask),
    INDEX ix_tasks_created_at  (created_at),
    -- 복합 인덱스 (자주 쓰는 필터 조합)
    INDEX ix_tasks_assignee_status  (assignee_id, status),
    INDEX ix_tasks_assigner_status  (assigner_id, status),
    INDEX ix_tasks_due_date_status  (due_date, status)
);

-- ============================================================
-- 업무-태그 연결
-- ============================================================
CREATE TABLE IF NOT EXISTS task_tags (
    task_id INT NOT NULL,
    tag_id  INT NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id)  REFERENCES tags(id)  ON DELETE CASCADE
);

-- ============================================================
-- [NEW v2] 업무 즐겨찾기
-- ============================================================
CREATE TABLE IF NOT EXISTS task_favorites (
    user_id    INT NOT NULL,
    task_id    INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, task_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- ============================================================
-- 첨부파일
-- ============================================================
CREATE TABLE IF NOT EXISTS attachments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    task_id     INT NOT NULL,
    uploader_id INT NOT NULL,
    filename    VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    file_size   BIGINT,
    mime_type   VARCHAR(100),
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id)     REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (uploader_id) REFERENCES users(id)
);

-- ============================================================
-- 업무 이력 로그
-- ============================================================
CREATE TABLE IF NOT EXISTS task_logs (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    task_id    INT NOT NULL,
    user_id    INT NOT NULL,
    action     VARCHAR(100) NOT NULL,
    old_value  VARCHAR(255),
    new_value  VARCHAR(255),
    comment    TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX ix_task_logs_task_id (task_id)
);

-- ============================================================
-- [NEW v2] 댓글 @멘션
-- ============================================================
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

-- ============================================================
-- 알림
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    task_id    INT,
    type       VARCHAR(50) NOT NULL,
    message    TEXT NOT NULL,
    is_read    BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    INDEX ix_notifications_user_id (user_id),
    INDEX ix_notifications_is_read (is_read)
);

-- ============================================================
-- 기본 시드 데이터
-- ============================================================

-- 기본 카테고리
INSERT IGNORE INTO categories (name, color) VALUES
    ('기획',     '#6366f1'),
    ('개발',     '#3b82f6'),
    ('영업',     '#10b981'),
    ('디자인',   '#f59e0b'),
    ('총무/인사', '#ef4444'),
    ('기타',     '#6b7280');

-- 기본 부서 (관리자 페이지에서 추가·수정 가능)
INSERT IGNORE INTO departments (name) VALUES
    ('현장소장'),
    ('공무팀'),
    ('공사팀'),
    ('안전팀'),
    ('품질팀'),
    ('직영팀');

-- 시스템 전역 설정 기본값
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
