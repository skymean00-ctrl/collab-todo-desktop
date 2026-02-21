-- ============================================================
-- Collab Todo - MySQL Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS collab_todo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE collab_todo;

-- 부서
CREATE TABLE departments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 사용자
CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name          VARCHAR(100) NOT NULL,
    department_id INT,
    job_title     VARCHAR(100),              -- 직함 (대리, 과장, 팀장 등)
    is_active     BOOLEAN DEFAULT TRUE,
    is_admin      BOOLEAN DEFAULT FALSE,
    is_verified   BOOLEAN DEFAULT FALSE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- 카테고리 (업무 분류)
CREATE TABLE categories (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    color      VARCHAR(7) DEFAULT '#6366f1'  -- hex color
);

-- 업무
CREATE TABLE tasks (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    content         TEXT,
    assigner_id     INT NOT NULL,            -- 지시자
    assignee_id     INT NOT NULL,            -- 담당자
    category_id     INT,
    priority        ENUM('urgent','high','normal','low') DEFAULT 'normal',
    status          ENUM('pending','in_progress','review','approved','rejected') DEFAULT 'pending',
    progress        TINYINT DEFAULT 0,       -- 0~100
    estimated_hours DECIMAL(5,2),           -- 예상 소요시간
    due_date        DATE,
    parent_task_id  INT,                    -- 자료요청 시 상위 업무 참조
    is_subtask      BOOLEAN DEFAULT FALSE,  -- 자료요청 여부
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (assigner_id) REFERENCES users(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
);

-- 태그
CREATE TABLE tags (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- 업무-태그 연결
CREATE TABLE task_tags (
    task_id INT NOT NULL,
    tag_id  INT NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 첨부파일
CREATE TABLE attachments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    task_id     INT NOT NULL,
    uploader_id INT NOT NULL,
    filename    VARCHAR(255) NOT NULL,       -- 원본 파일명
    stored_name VARCHAR(255) NOT NULL,       -- 서버 저장 파일명 (uuid)
    file_size   BIGINT,                      -- bytes
    mime_type   VARCHAR(100),
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (uploader_id) REFERENCES users(id)
);

-- 업무 이력 로그
CREATE TABLE task_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    task_id     INT NOT NULL,
    user_id     INT NOT NULL,
    action      VARCHAR(100) NOT NULL,       -- 상태변경, 코멘트, 파일첨부 등
    old_value   VARCHAR(255),
    new_value   VARCHAR(255),
    comment     TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 알림
CREATE TABLE notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    task_id    INT,
    type       VARCHAR(50) NOT NULL,         -- assigned, status_changed, due_soon, rejected 등
    message    TEXT NOT NULL,
    is_read    BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- 이메일 인증 토큰
CREATE TABLE email_verification_tokens (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    token      VARCHAR(100) NOT NULL UNIQUE,
    used       BOOLEAN DEFAULT FALSE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 기본 카테고리 삽입
INSERT INTO categories (name, color) VALUES
    ('기획', '#6366f1'),
    ('개발', '#3b82f6'),
    ('영업', '#10b981'),
    ('디자인', '#f59e0b'),
    ('총무/인사', '#ef4444'),
    ('기타', '#6b7280');
