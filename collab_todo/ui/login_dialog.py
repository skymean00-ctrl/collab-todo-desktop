"""로그인 다이얼로그."""

from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal

from collab_todo.models import User


class LoginDialog(QDialog):
    """
    로그인 화면.

    Signals:
        login_success(User): 로그인 성공 시 User 객체 전달
        register_requested(): 가입 화면 전환 요청
    """

    login_success = pyqtSignal(object)  # User
    register_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._logged_in_user: Optional[User] = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("로그인")
        self.setModal(True)
        self.setFixedSize(360, 240)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 타이틀
        title = QLabel("Collab To-Do 로그인")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)

        # 입력 폼
        form = QFormLayout()
        form.setSpacing(8)

        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("아이디 입력")
        form.addRow("아이디:", self._username_edit)

        self._password_edit = QLineEdit()
        self._password_edit.setPlaceholderText("비밀번호 입력")
        self._password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("비밀번호:", self._password_edit)

        layout.addLayout(form)

        # 오류 메시지
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: red; font-size: 12px;")
        self._error_label.setAlignment(Qt.AlignCenter)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        # 버튼
        btn_layout = QHBoxLayout()

        self._login_btn = QPushButton("로그인")
        self._login_btn.setDefault(True)
        self._login_btn.clicked.connect(self._on_login_clicked)

        self._register_btn = QPushButton("가입 신청")
        self._register_btn.clicked.connect(self._on_register_clicked)

        btn_layout.addWidget(self._login_btn)
        btn_layout.addWidget(self._register_btn)
        layout.addLayout(btn_layout)

        # Enter 키로 로그인
        self._password_edit.returnPressed.connect(self._on_login_clicked)

    def _on_login_clicked(self) -> None:
        username = self._username_edit.text().strip()
        password = self._password_edit.text()

        if not username or not password:
            self._show_error("아이디와 비밀번호를 입력하세요.")
            return

        self._try_login(username, password)

    def _try_login(self, username: str, password: str) -> None:
        """실제 로그인 시도. DB 연결은 외부에서 주입."""
        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection, DatabaseConnectionError
        from collab_todo.services.auth_service import login, check_pending

        config = load_db_config()
        if config is None:
            self._show_error("DB 설정이 없습니다.")
            return

        try:
            with db_connection(config) as conn:
                user = login(conn, username, password)
                if user is not None:
                    self._logged_in_user = user
                    self.login_success.emit(user)
                    self.accept()
                    return

                if check_pending(conn, username, password):
                    self._show_error("관리자 승인 대기 중입니다.")
                else:
                    self._show_error("아이디 또는 비밀번호가 틀렸습니다.")

        except DatabaseConnectionError:
            self._show_error("DB 연결에 실패했습니다.")

    def _on_register_clicked(self) -> None:
        self.register_requested.emit()
        self.reject()

    def _show_error(self, msg: str) -> None:
        self._error_label.setText(msg)
        self._error_label.show()

    def get_logged_in_user(self) -> Optional[User]:
        return self._logged_in_user
