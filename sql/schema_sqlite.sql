-- SQLite 초기 스키마
-- NAS MySQL 없이 로컬에서 독립 실행하기 위한 스키마

CREATE TABLE IF NOT EXISTS users (
    id           INTEGER  PRIMARY KEY AUTOINCREMENT,
    username     TEXT     NOT NULL UNIQUE,
    display_name TEXT     NOT NULL,
    email        TEXT     NOT NULL UNIQUE,
    role         TEXT     NOT NULL DEFAULT 'user',
    is_active    INTEGER  NOT NULL DEFAULT 1,
    created_at   DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at   DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    name        TEXT     NOT NULL,
    description TEXT,
    owner_id    INTEGER  NOT NULL REFERENCES users(id),
    is_archived INTEGER  NOT NULL DEFAULT 0,
    created_at  DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at  DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id                  INTEGER  PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER  NOT NULL REFERENCES projects(id),
    title               TEXT     NOT NULL,
    description         TEXT,
    author_id           INTEGER  NOT NULL REFERENCES users(id),
    current_assignee_id INTEGER  NOT NULL REFERENCES users(id),
    next_assignee_id    INTEGER  REFERENCES users(id),
    status              TEXT     NOT NULL DEFAULT 'pending',
    due_date            DATETIME,
    completed_at        DATETIME,
    created_at          DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at          DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS task_history (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    task_id     INTEGER  NOT NULL REFERENCES tasks(id),
    actor_id    INTEGER  NOT NULL REFERENCES users(id),
    action_type TEXT     NOT NULL,
    old_status  TEXT,
    new_status  TEXT,
    note        TEXT,
    created_at  DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notifications (
    id                INTEGER  PRIMARY KEY AUTOINCREMENT,
    recipient_id      INTEGER  NOT NULL REFERENCES users(id),
    task_id           INTEGER  REFERENCES tasks(id),
    notification_type TEXT     NOT NULL,
    message           TEXT     NOT NULL,
    is_read           INTEGER  NOT NULL DEFAULT 0,
    created_at        DATETIME NOT NULL DEFAULT (datetime('now')),
    read_at           DATETIME
);
