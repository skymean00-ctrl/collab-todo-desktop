"""알림 패널 위젯."""

from __future__ import annotations

from typing import List

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
)
from PyQt5.QtCore import Qt

from collab_todo.models import Notification


class NotificationWidget(QWidget):
    """
    알림 패널.

    - 미읽음 알림 목록 표시
    - 전체 읽음 처리
    - 새로고침
    """

    def __init__(self, *, user_id: int, parent=None) -> None:
        super().__init__(parent)
        self._user_id = user_id
        self._notifications: List[Notification] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 상단: 제목 + 배지
        top = QHBoxLayout()
        self._title_label = QLabel("알림")
        self._title_label.setStyleSheet("font-weight: bold;")
        top.addWidget(self._title_label)

        self._badge_label = QLabel("")
        self._badge_label.setStyleSheet(
            "color: white; background: red; border-radius: 8px; "
            "padding: 2px 6px; font-size: 11px;"
        )
        self._badge_label.hide()
        top.addWidget(self._badge_label)

        top.addStretch()

        self._read_all_btn = QPushButton("모두 읽음")
        self._read_all_btn.clicked.connect(self._on_mark_all_read)
        top.addWidget(self._read_all_btn)

        layout.addLayout(top)

        # 알림 목록
        self._list = QListWidget()
        layout.addWidget(self._list)

    def refresh(self) -> None:
        """DB에서 미읽음 알림을 가져온다."""
        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection, DatabaseConnectionError
        from collab_todo.repositories import list_notifications, count_unread

        config = load_db_config()
        if config is None:
            return

        try:
            with db_connection(config) as conn:
                self._notifications = list_notifications(
                    conn, self._user_id, unread_only=True, limit=50
                )
                unread = count_unread(conn, self._user_id)
        except DatabaseConnectionError:
            return

        self._populate_list()
        self._update_badge(unread)

    def set_notifications(self, notifications: List[Notification]) -> None:
        """외부에서 알림 데이터를 직접 설정 (동기화 시)."""
        self._notifications = list(notifications)
        self._populate_list()
        self._update_badge(len(self._notifications))

    def _populate_list(self) -> None:
        self._list.clear()
        for noti in self._notifications:
            time_str = noti.created_at.strftime("%m/%d %H:%M")
            item = QListWidgetItem(f"[{time_str}] {noti.message}")
            self._list.addItem(item)

        if not self._notifications:
            self._list.addItem(QListWidgetItem("새 알림이 없습니다."))

    def _update_badge(self, count: int) -> None:
        if count > 0:
            self._badge_label.setText(str(count))
            self._badge_label.show()
        else:
            self._badge_label.hide()

    def _on_mark_all_read(self) -> None:
        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection, DatabaseConnectionError
        from collab_todo.repositories import mark_all_as_read

        config = load_db_config()
        if config is None:
            return

        try:
            with db_connection(config) as conn:
                mark_all_as_read(conn, self._user_id)
        except DatabaseConnectionError:
            return

        self._notifications.clear()
        self._populate_list()
        self._update_badge(0)
