"""업무 상세 위젯 (우측 패널)."""

from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QTextEdit,
    QDateEdit,
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal

from collab_todo.models import Task


_STATUS_LABELS = {
    "pending": "확인 필요",
    "confirmed": "확인됨",
    "in_progress": "진행 중",
    "review": "검토",
    "completed": "완료",
    "on_hold": "보류",
    "cancelled": "취소",
}

# 상태별 가능한 전이
_STATUS_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["in_progress", "on_hold", "cancelled"],
    "in_progress": ["review", "completed", "on_hold"],
    "review": ["completed", "in_progress"],
    "on_hold": ["in_progress", "cancelled"],
}


class TaskDetailWidget(QWidget):
    """
    업무 상세 패널.

    - 업무 정보 표시
    - 상태 변경 버튼 (확인, 진행, 완료 등)
    - 확인 시 약속 기한 입력
    """

    task_updated = pyqtSignal()  # 상태 변경 후 목록 새로고침 요청

    def __init__(self, *, current_user_id: int, parent=None) -> None:
        super().__init__(parent)
        self._current_user_id = current_user_id
        self._task: Optional[Task] = None
        self._user_map: dict[int, str] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignTop)

        # 빈 상태 표시
        self._empty_label = QLabel("업무를 선택하세요")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("color: gray; font-size: 14px; padding: 40px;")
        self._layout.addWidget(self._empty_label)

        # 상세 정보 그룹 (초기에는 숨김)
        self._detail_group = QGroupBox()
        self._detail_group.hide()
        detail_layout = QVBoxLayout(self._detail_group)

        # 제목
        self._title_label = QLabel()
        self._title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._title_label.setWordWrap(True)
        detail_layout.addWidget(self._title_label)

        # 정보 폼
        info_form = QFormLayout()
        info_form.setSpacing(6)

        self._status_label = QLabel()
        info_form.addRow("상태:", self._status_label)

        self._author_label = QLabel()
        info_form.addRow("지시자:", self._author_label)

        self._assignee_label = QLabel()
        info_form.addRow("담당자:", self._assignee_label)

        self._next_assignee_label = QLabel()
        info_form.addRow("검토자:", self._next_assignee_label)

        self._due_date_label = QLabel()
        info_form.addRow("기한:", self._due_date_label)

        self._promised_date_label = QLabel()
        info_form.addRow("약속일:", self._promised_date_label)

        self._private_label = QLabel()
        info_form.addRow("공개:", self._private_label)

        detail_layout.addLayout(info_form)

        # 설명
        self._desc_label = QLabel()
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet("margin-top: 8px; padding: 8px; background: #f5f5f5;")
        detail_layout.addWidget(self._desc_label)

        # 액션 버튼 영역
        self._action_layout = QHBoxLayout()
        detail_layout.addLayout(self._action_layout)

        # 첨부파일 영역
        from collab_todo.ui.attachment_widget import AttachmentWidget

        self._attachment_widget = AttachmentWidget(user_id=self._current_user_id)
        detail_layout.addWidget(self._attachment_widget)

        self._layout.addWidget(self._detail_group)

    def set_user_map(self, user_map: dict[int, str]) -> None:
        self._user_map = user_map

    def show_task(self, task: Task) -> None:
        """선택된 업무 표시."""
        self._task = task
        self._empty_label.hide()
        self._detail_group.show()

        self._title_label.setText(task.title)
        self._status_label.setText(_STATUS_LABELS.get(task.status, task.status))
        self._author_label.setText(self._user_map.get(task.author_id, str(task.author_id)))
        self._assignee_label.setText(
            self._user_map.get(task.current_assignee_id, str(task.current_assignee_id))
        )

        if task.next_assignee_id:
            self._next_assignee_label.setText(
                self._user_map.get(task.next_assignee_id, str(task.next_assignee_id))
            )
        else:
            self._next_assignee_label.setText("-")

        self._due_date_label.setText(
            task.due_date.strftime("%Y-%m-%d") if task.due_date else "-"
        )
        self._promised_date_label.setText(
            task.promised_date.strftime("%Y-%m-%d") if task.promised_date else "-"
        )
        self._private_label.setText("비공개" if task.is_private else "공개")
        self._desc_label.setText(task.description or "(설명 없음)")

        self._build_action_buttons(task)
        self._attachment_widget.set_task(task.id)

    def clear(self) -> None:
        self._task = None
        self._empty_label.show()
        self._detail_group.hide()

    def _build_action_buttons(self, task: Task) -> None:
        """현재 상태에 따라 가능한 액션 버튼을 생성한다."""
        # 기존 버튼 제거
        while self._action_layout.count():
            item = self._action_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if task.status in ("completed", "cancelled"):
            return

        # 확인 (pending → confirmed): 담당자만
        if task.status == "pending" and task.current_assignee_id == self._current_user_id:
            confirm_btn = QPushButton("확인 (기한 약속)")
            confirm_btn.clicked.connect(self._on_confirm)
            self._action_layout.addWidget(confirm_btn)

        # 상태 전이 버튼
        transitions = _STATUS_TRANSITIONS.get(task.status, [])
        for new_status in transitions:
            if new_status == "confirmed":
                continue  # 위에서 별도 처리
            btn = QPushButton(_STATUS_LABELS.get(new_status, new_status))
            btn.clicked.connect(lambda checked, s=new_status: self._on_status_change(s))
            self._action_layout.addWidget(btn)

        # 완료 버튼 (별도 로직: 검토자 있으면 forward)
        if task.status in ("in_progress", "review"):
            complete_btn = QPushButton("완료 처리")
            complete_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            complete_btn.clicked.connect(self._on_complete)
            self._action_layout.addWidget(complete_btn)

    def _on_confirm(self) -> None:
        """확인 + 약속 기한 입력."""
        if self._task is None:
            return

        from PyQt5.QtWidgets import QDialog, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("업무 확인 - 기한 약속")
        dialog.setFixedSize(300, 150)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("완료 약속 날짜를 선택하세요:"))

        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate().addDays(7))
        layout.addWidget(date_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec_() != QDialog.Accepted:
            return

        promised_date = date_edit.date().toPyDate()

        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection
        from collab_todo.repositories import confirm_task
        from datetime import datetime

        config = load_db_config()
        if config is None:
            return

        with db_connection(config) as conn:
            confirm_task(
                conn,
                task_id=self._task.id,
                actor_id=self._current_user_id,
                promised_date=datetime.combine(promised_date, datetime.min.time()),
            )

        self.task_updated.emit()

    def _on_status_change(self, new_status: str) -> None:
        if self._task is None:
            return

        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection
        from collab_todo.repositories import update_task_status

        config = load_db_config()
        if config is None:
            return

        with db_connection(config) as conn:
            update_task_status(
                conn,
                task_id=self._task.id,
                actor_id=self._current_user_id,
                new_status=new_status,
            )

        self.task_updated.emit()

    def _on_complete(self) -> None:
        if self._task is None:
            return

        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection
        from collab_todo.repositories import complete_task

        config = load_db_config()
        if config is None:
            return

        with db_connection(config) as conn:
            complete_task(
                conn,
                task_id=self._task.id,
                actor_id=self._current_user_id,
            )

        self.task_updated.emit()
