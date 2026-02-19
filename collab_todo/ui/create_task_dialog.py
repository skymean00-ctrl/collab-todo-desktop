"""업무 생성 다이얼로그."""

from __future__ import annotations

from typing import List, Optional

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDateEdit,
    QCheckBox,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QDate

from collab_todo.models import User, Project


class CreateTaskDialog(QDialog):
    """업무 생성 화면."""

    def __init__(
        self,
        *,
        current_user: User,
        users: List[User],
        projects: List[Project],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._current_user = current_user
        self._users = users
        self._projects = projects
        self._result_data: Optional[dict] = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("새 업무 생성")
        self.setModal(True)
        self.setMinimumSize(440, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(8)

        # 프로젝트 선택
        self._project_combo = QComboBox()
        for proj in self._projects:
            self._project_combo.addItem(proj.name, proj.id)
        form.addRow("프로젝트:", self._project_combo)

        # 제목
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("업무 제목")
        form.addRow("제목:", self._title_edit)

        # 설명
        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("업무 설명 (선택)")
        self._desc_edit.setMaximumHeight(100)
        form.addRow("설명:", self._desc_edit)

        # 담당자
        self._assignee_combo = QComboBox()
        for user in self._users:
            self._assignee_combo.addItem(
                f"{user.display_name} ({user.username})", user.id
            )
        form.addRow("담당자:", self._assignee_combo)

        # 다음 담당자 (검토자)
        self._next_assignee_combo = QComboBox()
        self._next_assignee_combo.addItem("없음 (바로 완료)", 0)
        for user in self._users:
            self._next_assignee_combo.addItem(
                f"{user.display_name} ({user.username})", user.id
            )
        form.addRow("검토자:", self._next_assignee_combo)

        # 기한
        self._due_date_check = QCheckBox("기한 설정")
        self._due_date_edit = QDateEdit()
        self._due_date_edit.setCalendarPopup(True)
        self._due_date_edit.setDate(QDate.currentDate().addDays(7))
        self._due_date_edit.setEnabled(False)
        self._due_date_check.toggled.connect(self._due_date_edit.setEnabled)

        due_layout = QHBoxLayout()
        due_layout.addWidget(self._due_date_check)
        due_layout.addWidget(self._due_date_edit)
        form.addRow("기한:", due_layout)

        # 비공개
        self._private_check = QCheckBox("비공개 업무")
        form.addRow("", self._private_check)

        layout.addLayout(form)

        # 오류 표시
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: red;")
        self._error_label.setAlignment(Qt.AlignCenter)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        # 버튼
        btn_layout = QHBoxLayout()
        self._create_btn = QPushButton("생성")
        self._create_btn.setDefault(True)
        self._create_btn.clicked.connect(self._on_create)

        self._cancel_btn = QPushButton("취소")
        self._cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self._create_btn)
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

    def _on_create(self) -> None:
        title = self._title_edit.text().strip()
        if not title:
            self._show_error("제목을 입력하세요.")
            return

        if self._project_combo.count() == 0:
            self._show_error("프로젝트가 없습니다.")
            return

        project_id = self._project_combo.currentData()
        description = self._desc_edit.toPlainText().strip() or None
        assignee_id = self._assignee_combo.currentData()

        next_assignee_id = self._next_assignee_combo.currentData()
        if next_assignee_id == 0:
            next_assignee_id = None

        due_date = None
        if self._due_date_check.isChecked():
            qdate = self._due_date_edit.date()
            due_date = qdate.toPyDate()

        is_private = self._private_check.isChecked()

        self._result_data = {
            "project_id": project_id,
            "title": title,
            "description": description,
            "author_id": self._current_user.id,
            "current_assignee_id": assignee_id,
            "next_assignee_id": next_assignee_id,
            "due_date": due_date,
            "is_private": is_private,
        }
        self.accept()

    def get_task_data(self) -> Optional[dict]:
        return self._result_data

    def _show_error(self, msg: str) -> None:
        self._error_label.setText(msg)
        self._error_label.show()
