"""리포지토리 패키지. 기존 코드 호환을 위해 주요 함수 re-export."""

from .user_repo import (
    get_user_by_id,
    get_user_by_username,
    get_password_hash,
    list_active_users,
    list_pending_users,
    create_user,
    activate_user,
    deactivate_user,
)
from .project_repo import list_projects_for_user
from .task_repo import (
    get_task_by_id,
    list_tasks_for_assignee,
    list_tasks_created_by_user,
    create_task,
    update_task_status,
    confirm_task,
    complete_task,
)
from .subtask_repo import list_subtasks, create_subtask, count_subtasks
from .attachment_repo import (
    list_attachments,
    list_attachments_with_subtasks,
    create_attachment,
    delete_attachment,
)
from .viewer_repo import (
    list_viewer_ids,
    add_viewer,
    add_viewers,
    remove_viewer,
    can_view_task,
)
from .history_repo import list_task_history
from .notification_repo import (
    list_notifications,
    count_unread,
    create_notification,
    mark_as_read,
    mark_all_as_read,
)

__all__ = [
    # user
    "get_user_by_id",
    "get_user_by_username",
    "get_password_hash",
    "list_active_users",
    "list_pending_users",
    "create_user",
    "activate_user",
    "deactivate_user",
    # project
    "list_projects_for_user",
    # task
    "get_task_by_id",
    "list_tasks_for_assignee",
    "list_tasks_created_by_user",
    "create_task",
    "update_task_status",
    "confirm_task",
    "complete_task",
    # subtask
    "list_subtasks",
    "create_subtask",
    "count_subtasks",
    # attachment
    "list_attachments",
    "list_attachments_with_subtasks",
    "create_attachment",
    "delete_attachment",
    # viewer
    "list_viewer_ids",
    "add_viewer",
    "add_viewers",
    "remove_viewer",
    "can_view_task",
    # history
    "list_task_history",
    # notification
    "list_notifications",
    "count_unread",
    "create_notification",
    "mark_as_read",
    "mark_all_as_read",
]
