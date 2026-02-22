"""v2 신규 테이블: refresh_tokens, user_notification_preferences, filter_presets,
system_settings, task_favorites, mentions, password_reset_tokens
및 tasks/notifications 인덱스 추가

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── refresh_tokens ──────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id",         sa.Integer(),     nullable=False),
        sa.Column("user_id",    sa.Integer(),     nullable=False),
        sa.Column("token",      sa.String(128),   nullable=False),
        sa.Column("expires_at", sa.DateTime(),    nullable=False),
        sa.Column("revoked",    sa.Boolean(),     server_default="0"),
        sa.Column("created_at", sa.DateTime(),    server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_refresh_tokens_token",   "refresh_tokens", ["token"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ── user_notification_preferences ───────────────────────
    op.create_table(
        "user_notification_preferences",
        sa.Column("user_id",               sa.Integer(), nullable=False),
        sa.Column("notify_assigned",       sa.Boolean(), server_default="1"),
        sa.Column("notify_status_changed", sa.Boolean(), server_default="1"),
        sa.Column("notify_due_soon",       sa.Boolean(), server_default="1"),
        sa.Column("notify_mentioned",      sa.Boolean(), server_default="1"),
        sa.Column("notify_reassigned",     sa.Boolean(), server_default="1"),
        sa.Column("notify_commented",      sa.Boolean(), server_default="1"),
        sa.Column("email_assigned",        sa.Boolean(), server_default="1"),
        sa.Column("email_status_changed",  sa.Boolean(), server_default="1"),
        sa.Column("email_due_soon",        sa.Boolean(), server_default="1"),
        sa.Column("email_mentioned",       sa.Boolean(), server_default="1"),
        sa.Column("email_reassigned",      sa.Boolean(), server_default="1"),
        sa.Column("updated_at",            sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("user_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # ── filter_presets ──────────────────────────────────────
    op.create_table(
        "filter_presets",
        sa.Column("id",            sa.Integer(),     nullable=False),
        sa.Column("user_id",       sa.Integer(),     nullable=False),
        sa.Column("name",          sa.String(100),   nullable=False),
        sa.Column("section",       sa.String(50)),
        sa.Column("status",        sa.String(50)),
        sa.Column("priority",      sa.String(50)),
        sa.Column("sort_by",       sa.String(50)),
        sa.Column("sort_dir",      sa.String(10)),
        sa.Column("due_date_from", sa.Date()),
        sa.Column("due_date_to",   sa.Date()),
        sa.Column("created_at",    sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_filter_presets_user_id", "filter_presets", ["user_id"])

    # ── system_settings ─────────────────────────────────────
    op.create_table(
        "system_settings",
        sa.Column("key",         sa.String(100), nullable=False),
        sa.Column("value",       sa.Text(),      nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("updated_at",  sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("key"),
    )

    # ── task_favorites ──────────────────────────────────────
    op.create_table(
        "task_favorites",
        sa.Column("user_id",    sa.Integer(), nullable=False),
        sa.Column("task_id",    sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("user_id", "task_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
    )

    # ── mentions ────────────────────────────────────────────
    op.create_table(
        "mentions",
        sa.Column("id",                sa.Integer(), nullable=False),
        sa.Column("log_id",            sa.Integer(), nullable=False),
        sa.Column("mentioned_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at",        sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["log_id"],            ["task_logs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mentioned_user_id"], ["users.id"],     ondelete="CASCADE"),
    )
    op.create_index("ix_mentions_log_id",            "mentions", ["log_id"])
    op.create_index("ix_mentions_mentioned_user_id", "mentions", ["mentioned_user_id"])

    # ── password_reset_tokens (v1에서 없을 수 있음) ─────────
    op.create_table(
        "password_reset_tokens",
        sa.Column("id",         sa.Integer(),   nullable=False),
        sa.Column("user_id",    sa.Integer(),   nullable=False),
        sa.Column("token",      sa.String(64),  nullable=False),
        sa.Column("used",       sa.Boolean(),   server_default="0"),
        sa.Column("expires_at", sa.DateTime(),  nullable=False),
        sa.Column("created_at", sa.DateTime(),  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_password_reset_tokens_token", "password_reset_tokens", ["token"])

    # ── tasks 복합 인덱스 추가 ──────────────────────────────
    op.create_index("ix_tasks_assignee_status", "tasks", ["assignee_id", "status"])
    op.create_index("ix_tasks_assigner_status", "tasks", ["assigner_id", "status"])
    op.create_index("ix_tasks_due_date_status", "tasks", ["due_date",    "status"])

    # ── notifications is_read 인덱스 ────────────────────────
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])

    # ── 기본 시드 데이터 ────────────────────────────────────
    op.execute("""
        INSERT IGNORE INTO departments (name) VALUES
        ('현장소장'), ('공무팀'), ('공사팀'), ('안전팀'), ('품질팀'), ('직영팀')
    """)
    op.execute("""
        INSERT IGNORE INTO system_settings (`key`, value, description) VALUES
        ('access_token_expire_minutes', '60',   'Access JWT 만료 시간 (분)'),
        ('refresh_token_expire_days',   '7',    'Refresh Token 만료 일수'),
        ('max_upload_size_mb',          '10',   '파일 업로드 최대 크기 (MB)'),
        ('allowed_file_types',
         'pdf,docx,xlsx,pptx,jpg,jpeg,png,gif,zip,hwp',
         '허용 파일 확장자 (쉼표 구분)'),
        ('max_refresh_tokens_per_user', '5',    '사용자 당 최대 Refresh Token 수'),
        ('rate_limit_per_minute',       '200',  '분당 API 요청 제한'),
        ('due_soon_days_warning',       '3',    '마감 임박 경고 일수'),
        ('max_filter_presets',          '10',   '사용자 당 최대 필터 프리셋 수'),
        ('app_name',                    'CollabTodo', '서비스 이름'),
        ('app_version',                 '2.0.0', '현재 버전')
    """)


def downgrade() -> None:
    # 인덱스 제거
    op.drop_index("ix_notifications_is_read",   table_name="notifications")
    op.drop_index("ix_tasks_due_date_status",   table_name="tasks")
    op.drop_index("ix_tasks_assigner_status",   table_name="tasks")
    op.drop_index("ix_tasks_assignee_status",   table_name="tasks")

    # 신규 테이블 제거
    op.drop_index("ix_password_reset_tokens_token", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_index("ix_mentions_mentioned_user_id", table_name="mentions")
    op.drop_index("ix_mentions_log_id",            table_name="mentions")
    op.drop_table("mentions")

    op.drop_table("task_favorites")
    op.drop_table("system_settings")

    op.drop_index("ix_filter_presets_user_id", table_name="filter_presets")
    op.drop_table("filter_presets")

    op.drop_table("user_notification_preferences")

    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token",   table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
