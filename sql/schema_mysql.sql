-- MySQL 초기 스키마 정의
-- 단일 조직(팀) 내에서 사용할 협업 To-Do 시스템 기준

CREATE TABLE IF NOT EXISTS users (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username     VARCHAR(50)     NOT NULL UNIQUE,
    display_name VARCHAR(100)    NOT NULL,
    email        VARCHAR(255)    NOT NULL,
    password_hash VARCHAR(255)   NOT NULL,
    role         ENUM('user', 'admin', 'supervisor') NOT NULL DEFAULT 'user',
    is_active    TINYINT(1)      NOT NULL DEFAULT 1,
    created_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS projects (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100)    NOT NULL,
    description  TEXT            NULL,
    owner_id     BIGINT UNSIGNED NOT NULL,
    is_archived  TINYINT(1)      NOT NULL DEFAULT 0,
    created_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_projects_owner FOREIGN KEY (owner_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS tasks (
    id                 BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id         BIGINT UNSIGNED NOT NULL,
    title              VARCHAR(200)    NOT NULL,
    description        TEXT            NULL,
    author_id          BIGINT UNSIGNED NOT NULL,
    current_assignee_id BIGINT UNSIGNED NOT NULL,
    next_assignee_id   BIGINT UNSIGNED NULL,
    status             ENUM('pending', 'in_progress', 'review', 'completed', 'on_hold', 'cancelled') NOT NULL DEFAULT 'pending',
    due_date           DATETIME        NULL,
    completed_at       DATETIME        NULL,
    created_at         TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_tasks_project FOREIGN KEY (project_id) REFERENCES projects(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_tasks_author FOREIGN KEY (author_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_tasks_current_assignee FOREIGN KEY (current_assignee_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_tasks_next_assignee FOREIGN KEY (next_assignee_id) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_tasks_project (project_id),
    INDEX idx_tasks_current_assignee (current_assignee_id),
    INDEX idx_tasks_author (author_id),
    INDEX idx_tasks_status (status),
    INDEX idx_tasks_due_date (due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS task_history (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    task_id     BIGINT UNSIGNED NOT NULL,
    actor_id    BIGINT UNSIGNED NOT NULL,
    action_type VARCHAR(50)     NOT NULL,
    old_status  VARCHAR(50)     NULL,
    new_status  VARCHAR(50)     NULL,
    note        TEXT            NULL,
    created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_task_history_task FOREIGN KEY (task_id) REFERENCES tasks(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_task_history_actor FOREIGN KEY (actor_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_task_history_task (task_id),
    INDEX idx_task_history_actor (actor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS notifications (
    id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    recipient_id      BIGINT UNSIGNED NOT NULL,
    task_id           BIGINT UNSIGNED NULL,
    notification_type VARCHAR(50)     NOT NULL,
    message           TEXT            NOT NULL,
    is_read           TINYINT(1)      NOT NULL DEFAULT 0,
    created_at        TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at           DATETIME        NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_notifications_recipient FOREIGN KEY (recipient_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_notifications_task FOREIGN KEY (task_id) REFERENCES tasks(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_notifications_recipient (recipient_id),
    INDEX idx_notifications_task (task_id),
    INDEX idx_notifications_is_read (is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


