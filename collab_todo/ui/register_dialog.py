"""가입 신청 다이얼로그."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QMessageBox,
)
from PyQt5.QtCore import Qt


class RegisterDialog(QDialog):
    """가입 신청 화면. 승인 전까지 로그인 불가."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("가입 신청")
        self.setModal(True)
        self.setFixedSize(380, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("새 계정 가입 신청")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)

        info = QLabel("가입 후 관리자 승인이 필요합니다.")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: gray; font-size: 11px; margin-bottom: 4px;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(8)

        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("영문/숫자, 3자 이상")
        form.addRow("아이디:", self._username_edit)

        self._display_name_edit = QLineEdit()
        self._display_name_edit.setPlaceholderText("표시 이름 (한글 가능)")
        form.addRow("이름:", self._display_name_edit)

        self._job_title_edit = QLineEdit()
        self._job_title_edit.setPlaceholderText("예: 경영지원, 개발, 디자인")
        form.addRow("담당업무:", self._job_title_edit)

        self._email_edit = QLineEdit()
        self._email_edit.setPlaceholderText("비밀번호 분실 시 필요")
        form.addRow("이메일:", self._email_edit)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.Password)
        self._password_edit.setPlaceholderText("6자 이상")
        form.addRow("비밀번호:", self._password_edit)

        self._password_confirm_edit = QLineEdit()
        self._password_confirm_edit.setEchoMode(QLineEdit.Password)
        form.addRow("비밀번호 확인:", self._password_confirm_edit)

        layout.addLayout(form)

        # 오류 메시지
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: red; font-size: 12px;")
        self._error_label.setAlignment(Qt.AlignCenter)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        # 버튼
        btn_layout = QHBoxLayout()

        self._submit_btn = QPushButton("가입 신청")
        self._submit_btn.setDefault(True)
        self._submit_btn.clicked.connect(self._on_submit)

        self._cancel_btn = QPushButton("취소")
        self._cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self._submit_btn)
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

    def _on_submit(self) -> None:
        username = self._username_edit.text().strip()
        display_name = self._display_name_edit.text().strip()
        job_title = self._job_title_edit.text().strip()
        email = self._email_edit.text().strip()
        password = self._password_edit.text()
        password_confirm = self._password_confirm_edit.text()

        # 검증
        if not username or len(username) < 3:
            self._show_error("아이디는 3자 이상이어야 합니다.")
            return
        if not display_name:
            self._show_error("이름을 입력하세요.")
            return
        if not job_title:
            self._show_error("담당업무를 입력하세요.")
            return
        if not email:
            self._show_error("이메일을 입력하세요. (비밀번호 분실 시 필요)")
            return
        if not password or len(password) < 6:
            self._show_error("비밀번호는 6자 이상이어야 합니다.")
            return
        if password != password_confirm:
            self._show_error("비밀번호가 일치하지 않습니다.")
            return

        self._try_register(username, display_name, job_title, email, password)

    def _try_register(
        self, username: str, display_name: str, job_title: str, email: str, password: str
    ) -> None:
        from collab_todo.config import load_db_config
        from collab_todo.db import db_connection, DatabaseConnectionError
        from collab_todo.services.auth_service import register

        config = load_db_config()
        if config is None:
            self._show_error("DB 설정이 없습니다.")
            return

        try:
            with db_connection(config) as conn:
                register(
                    conn,
                    username=username,
                    display_name=display_name,
                    password=password,
                    email=email,
                    job_title=job_title,
                )
                conn.commit()

            QMessageBox.information(
                self,
                "가입 신청 완료",
                "가입 신청이 완료되었습니다.\n관리자 승인 후 로그인할 수 있습니다.",
            )
            self.accept()

        except DatabaseConnectionError:
            self._show_error("DB 연결에 실패했습니다.")
        except ValueError as e:
            self._show_error(str(e))

    def _show_error(self, msg: str) -> None:
        self._error_label.setText(msg)
        self._error_label.show()
