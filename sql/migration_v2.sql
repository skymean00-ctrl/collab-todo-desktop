-- Migration v2: MVP 업무 흐름 관리 기능 추가
-- 실행 전 반드시 백업할 것

-- 0. users 테이블: 담당업무 컬럼 추가
ALTER TABLE users
  ADD COLUMN job_title VARCHAR(100) NOT NULL DEFAULT '' AFTER email;


-- 1. tasks 테이블: 하위 업무, 확인/약속, 공개/비공개 지원
ALTER TABLE tasks
  MODIFY COLUMN status ENUM(
    'pending',
    'confirmed',
    'in_progress',
    'review',
    'completed',
    'on_hold',
    'cancelled'
  ) NOT NULL DEFAULT 'pending',
  ADD COLUMN parent_task_id   BIGINT UNSIGNED NULL AFTER project_id,
  ADD COLUMN confirmed_at     DATETIME NULL AFTER due_date,
  ADD COLUMN promised_date    DATETIME NULL AFTER confirmed_at,
  ADD COLUMN is_private       TINYINT(1) NOT NULL DEFAULT 0 AFTER promised_date,
  ADD CONSTRAINT fk_tasks_parent FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  ADD INDEX idx_tasks_parent (parent_task_id);


-- 2. task_attachments: 업무별 파일 첨부
CREATE TABLE IF NOT EXISTS task_attachments (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    task_id       BIGINT UNSIGNED NOT NULL,
    uploader_id   BIGINT UNSIGNED NOT NULL,
    file_name     VARCHAR(255)    NOT NULL,
    file_path     VARCHAR(500)    NOT NULL,
    file_size     BIGINT UNSIGNED NOT NULL DEFAULT 0,
    mime_type     VARCHAR(100)    NULL,
    created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_attachments_task FOREIGN KEY (task_id) REFERENCES tasks(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_attachments_uploader FOREIGN KEY (uploader_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_attachments_task (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 3. task_viewers: 비공개 업무 열람 권한
CREATE TABLE IF NOT EXISTS task_viewers (
    id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    task_id   BIGINT UNSIGNED NOT NULL,
    user_id   BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_task_viewer (task_id, user_id),
    CONSTRAINT fk_viewers_task FOREIGN KEY (task_id) REFERENCES tasks(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_viewers_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
