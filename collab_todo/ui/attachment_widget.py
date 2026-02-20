"""첨부파일 목록 위젯 (업무 상세 내 표시)."""

from __future__ import annotations

import os
from typing import List, Optional

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt

from collab_todo.models import TaskAttachment


class AttachmentWidget(QWidget):
    """
    업무별 첨부파일 관리.

    - 첨부파일 목록
    - 파일 추가 (QFileDialog)
    - 파일 삭제
    """

    def __init__(self, *, user_id: int, parent=None) -> None:
        super().__init__(parent)
        self._user_id = user_id
        self._task_id: Optional[int] = None
        self._attachments: List[TaskAttachment] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.addWidget(QLabel("첨부파일"))
        header.addStretch()

        self._add_btn = QPushButton("+ 파일 추가")
        self._add_btn.clicked.connect(self._on_add_file)
        header.addWidget(self._add_btn)

        self._delete_btn = QPushButton("삭제")
        self._delete_btn.clicked.connect(self._on_delete_file)
        header.addWidget(self._delete_btn)

        layout.addLayout(header)

        self._list = QListWidget()
        layout.addWidget(self._list)

    def set_task(self, task_id: int) -> None:
        """업무 변경 시 첨부파일 목록 로드."""
        self._task_id = task_id
        self.refresh()

    def refresh(self) -> None:
        if self._task_id is None:
            return

        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection, DatabaseConnectionError
        from collab_todo.repositories import list_attachments

        config = load_db_config()
        if config is None:
            return

        try:
            with db_connection(config) as conn:
                self._attachments = list_attachments(conn, self._task_id)
        except DatabaseConnectionError:
            return

        self._populate_list()

    def _populate_list(self) -> None:
        self._list.clear()
        for att in self._attachments:
            size_str = self._format_size(att.file_size)
            item = QListWidgetItem(f"{att.file_name} ({size_str})")
            item.setData(Qt.UserRole, att.id)
            self._list.addItem(item)

        if not self._attachments:
            self._list.addItem(QListWidgetItem("첨부파일 없음"))

    def _on_add_file(self) -> None:
        if self._task_id is None:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "파일 선택", "", "모든 파일 (*.*)"
        )
        if not file_path:
            return

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # 실제 환경에서는 파일을 서버에 복사 후 경로 저장
        # MVP에서는 원본 경로를 그대로 저장
        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection, DatabaseConnectionError
        from collab_todo.repositories import create_attachment
        import mimetypes

        mime_type, _ = mimetypes.guess_type(file_path)

        config = load_db_config()
        if config is None:
            return

        try:
            with db_connection(config) as conn:
                create_attachment(
                    conn,
                    task_id=self._task_id,
                    uploader_id=self._user_id,
                    file_name=file_name,
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=mime_type,
                )
        except DatabaseConnectionError:
            QMessageBox.warning(self, "오류", "DB 연결에 실패했습니다.")
            return

        self.refresh()

    def _on_delete_file(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return

        att_id = item.data(Qt.UserRole)
        if att_id is None:
            return

        reply = QMessageBox.question(
            self, "삭제 확인", "선택한 첨부파일을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection, DatabaseConnectionError
        from collab_todo.repositories import delete_attachment

        config = load_db_config()
        if config is None:
            return

        try:
            with db_connection(config) as conn:
                delete_attachment(conn, att_id)
        except DatabaseConnectionError:
            QMessageBox.warning(self, "오류", "DB 연결에 실패했습니다.")
            return

        self.refresh()

    @staticmethod
    def _format_size(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
