"""업무 목록 위젯 (좌측 패널)."""

from __future__ import annotations

from typing import List, Optional

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QComboBox,
    QHeaderView,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal

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


class TaskListWidget(QWidget):
    """
    업무 목록 패널.

    - '내가 담당' / '내가 지시' 탭 전환
    - 업무 클릭 시 task_selected 시그널
    - 새 업무 버튼
    """

    task_selected = pyqtSignal(object)  # Task
    create_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._tasks: List[Task] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 상단: 필터 + 새 업무 버튼
        top = QHBoxLayout()

        self._view_combo = QComboBox()
        self._view_combo.addItems(["내가 담당", "내가 지시"])
        self._view_combo.currentIndexChanged.connect(self._on_view_changed)
        top.addWidget(QLabel("보기:"))
        top.addWidget(self._view_combo)

        top.addStretch()

        self._create_btn = QPushButton("+ 새 업무")
        self._create_btn.clicked.connect(self.create_requested.emit)
        top.addWidget(self._create_btn)

        layout.addLayout(top)

        # 테이블
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["제목", "상태", "담당자", "기한"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self._table)

    def set_tasks(self, tasks: List[Task], user_map: dict[int, str] | None = None) -> None:
        """업무 목록을 표시한다."""
        self._tasks = list(tasks)
        self._user_map = user_map or {}
        self._populate_table()

    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._tasks))
        for i, task in enumerate(self._tasks):
            self._table.setItem(i, 0, QTableWidgetItem(task.title))

            status_text = _STATUS_LABELS.get(task.status, task.status)
            status_item = QTableWidgetItem(status_text)
            self._table.setItem(i, 1, status_item)

            assignee_name = self._user_map.get(task.current_assignee_id, str(task.current_assignee_id))
            self._table.setItem(i, 2, QTableWidgetItem(assignee_name))

            due_text = task.due_date.strftime("%Y-%m-%d") if task.due_date else "-"
            self._table.setItem(i, 3, QTableWidgetItem(due_text))

    def _on_cell_clicked(self, row: int, _col: int) -> None:
        if 0 <= row < len(self._tasks):
            self.task_selected.emit(self._tasks[row])

    def _on_view_changed(self, _index: int) -> None:
        """뷰 변경 시그널. 부모에서 데이터를 다시 로드해야 한다."""
        # 부모가 refresh를 호출해 줄 것을 기대
        pass

    @property
    def current_view(self) -> str:
        """'assignee' 또는 'author'."""
        return "assignee" if self._view_combo.currentIndex() == 0 else "author"

    @property
    def view_combo(self) -> QComboBox:
        return self._view_combo
