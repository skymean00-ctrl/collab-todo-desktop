"""사용자 관리 위젯 (관리자 전용)."""

from __future__ import annotations

from typing import List

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt

from collab_todo.models import User


class UserManagementWidget(QWidget):
    """
    관리자용 사용자 관리 패널.

    - 승인 대기 사용자 목록
    - 승인/거절 버튼
    - 활성 사용자 목록 + 비활성화
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # === 승인 대기 섹션 ===
        pending_label = QLabel("승인 대기 사용자")
        pending_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(pending_label)

        self._pending_table = QTableWidget(0, 5)
        self._pending_table.setHorizontalHeaderLabels(
            ["아이디", "이름", "직책", "이메일", "신청일"]
        )
        self._pending_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self._pending_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._pending_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._pending_table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self._pending_table)

        pending_btn_layout = QHBoxLayout()
        self._approve_btn = QPushButton("승인")
        self._approve_btn.clicked.connect(self._on_approve)
        self._reject_btn = QPushButton("거절")
        self._reject_btn.clicked.connect(self._on_reject)
        self._refresh_btn = QPushButton("새로고침")
        self._refresh_btn.clicked.connect(self.refresh)

        pending_btn_layout.addWidget(self._approve_btn)
        pending_btn_layout.addWidget(self._reject_btn)
        pending_btn_layout.addStretch()
        pending_btn_layout.addWidget(self._refresh_btn)
        layout.addLayout(pending_btn_layout)

        # === 활성 사용자 섹션 ===
        active_label = QLabel("활성 사용자")
        active_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; margin-top: 12px;"
        )
        layout.addWidget(active_label)

        self._active_table = QTableWidget(0, 5)
        self._active_table.setHorizontalHeaderLabels(
            ["아이디", "이름", "직책", "역할", "가입일"]
        )
        self._active_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._active_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._active_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._active_table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self._active_table)

        active_btn_layout = QHBoxLayout()
        self._deactivate_btn = QPushButton("비활성화")
        self._deactivate_btn.clicked.connect(self._on_deactivate)
        active_btn_layout.addWidget(self._deactivate_btn)
        active_btn_layout.addStretch()
        layout.addLayout(active_btn_layout)

        # 데이터 저장용
        self._pending_users: List[User] = []
        self._active_users: List[User] = []

    def refresh(self) -> None:
        """DB에서 사용자 목록을 다시 불러온다."""
        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection, DatabaseConnectionError
        from collab_todo.repositories import list_pending_users, list_active_users

        config = load_db_config()
        if config is None:
            return

        try:
            with db_connection(config) as conn:
                self._pending_users = list_pending_users(conn)
                self._active_users = list_active_users(conn)
        except DatabaseConnectionError:
            QMessageBox.warning(self, "오류", "DB 연결에 실패했습니다.")
            return

        self._populate_pending_table()
        self._populate_active_table()

    def _populate_pending_table(self) -> None:
        self._pending_table.setRowCount(len(self._pending_users))
        for i, user in enumerate(self._pending_users):
            self._pending_table.setItem(i, 0, QTableWidgetItem(user.username))
            self._pending_table.setItem(i, 1, QTableWidgetItem(user.display_name))
            self._pending_table.setItem(i, 2, QTableWidgetItem(user.position))
            self._pending_table.setItem(i, 3, QTableWidgetItem(user.email))
            self._pending_table.setItem(
                i, 4, QTableWidgetItem(user.created_at.strftime("%Y-%m-%d %H:%M"))
            )

    def _populate_active_table(self) -> None:
        self._active_table.setRowCount(len(self._active_users))
        for i, user in enumerate(self._active_users):
            self._active_table.setItem(i, 0, QTableWidgetItem(user.username))
            self._active_table.setItem(i, 1, QTableWidgetItem(user.display_name))
            self._active_table.setItem(i, 2, QTableWidgetItem(user.position))
            self._active_table.setItem(i, 3, QTableWidgetItem(user.role))
            self._active_table.setItem(
                i, 4, QTableWidgetItem(user.created_at.strftime("%Y-%m-%d %H:%M"))
            )

    def _get_selected_pending_user(self) -> User | None:
        row = self._pending_table.currentRow()
        if row < 0 or row >= len(self._pending_users):
            return None
        return self._pending_users[row]

    def _get_selected_active_user(self) -> User | None:
        row = self._active_table.currentRow()
        if row < 0 or row >= len(self._active_users):
            return None
        return self._active_users[row]

    def _on_approve(self) -> None:
        user = self._get_selected_pending_user()
        if user is None:
            QMessageBox.information(self, "선택 필요", "승인할 사용자를 선택하세요.")
            return

        reply = QMessageBox.question(
            self,
            "승인 확인",
            f"'{user.display_name}' ({user.username})을(를) 승인하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection
        from collab_todo.repositories import activate_user

        config = load_db_config()
        if config is None:
            return

        with db_connection(config) as conn:
            activate_user(conn, user.id)

        self.refresh()

    def _on_reject(self) -> None:
        user = self._get_selected_pending_user()
        if user is None:
            QMessageBox.information(self, "선택 필요", "거절할 사용자를 선택하세요.")
            return

        reply = QMessageBox.question(
            self,
            "거절 확인",
            f"'{user.display_name}' ({user.username})의 가입을 거절하시겠습니까?\n"
            "이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection
        from collab_todo.repositories import deactivate_user

        config = load_db_config()
        if config is None:
            return

        with db_connection(config) as conn:
            deactivate_user(conn, user.id)

        self.refresh()

    def _on_deactivate(self) -> None:
        user = self._get_selected_active_user()
        if user is None:
            QMessageBox.information(
                self, "선택 필요", "비활성화할 사용자를 선택하세요."
            )
            return

        if user.role == "admin":
            QMessageBox.warning(self, "불가", "관리자는 비활성화할 수 없습니다.")
            return

        reply = QMessageBox.question(
            self,
            "비활성화 확인",
            f"'{user.display_name}' ({user.username})을(를) 비활성화하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection
        from collab_todo.repositories import deactivate_user

        config = load_db_config()
        if config is None:
            return

        with db_connection(config) as conn:
            deactivate_user(conn, user.id)

        self.refresh()
