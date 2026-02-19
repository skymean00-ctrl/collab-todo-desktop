import sys
from datetime import datetime
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QStatusBar,
    QMessageBox,
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QAction,
    QDialog,
    QDialogButtonBox,
    QComboBox,
    QVBoxLayout,
    QFormLayout,
)
from PyQt5.QtCore import Qt, QTimer

from collab_todo.config import load_db_config, load_ai_service_config
from collab_todo.db import db_connection, DatabaseConnectionError
from collab_todo.sync import SyncState, perform_sync
from collab_todo.dashboard import summarize_tasks
from collab_todo.ai_client import AiSummaryConfig, summarize_text, AiSummaryError
from collab_todo.repositories import list_active_users
from collab_todo.models import User


class MainWindow(QMainWindow):
    """
    애플리케이션의 기본 메인 창.

    초기 단계에서는 단순히 창이 정상적으로 뜨는지,
    상태바에 간단한 메시지를 표시할 수 있는지만 확인한다.
    이후 단계에서 대시보드, 메뉴, 연결 상태 표시 등을 확장한다.
    """

    def __init__(self, *, window_title: str = "Collab To-Do Desktop") -> None:
        super().__init__()

        self._window_title: str = window_title
        self._status_bar: Optional[QStatusBar] = None
        self._last_sync_label: Optional[QLabel] = None
        self._connection_label: Optional[QLabel] = None
        self._sync_timer: Optional[QTimer] = None
        self._sync_state: SyncState = SyncState(last_synced_at=None)
        self._current_user_id: Optional[int] = None

        self._init_ui()
        self._init_sync()
        self._init_dashboard()
        self._init_user_selection()

    def _init_ui(self) -> None:
        """기본 UI 구성 요소를 초기화한다."""
        self.setWindowTitle(self._window_title)
        self.resize(1024, 640)

        label = QLabel("Collab To-Do Desktop", self)
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)

        status_bar = QStatusBar(self)
        self._connection_label = QLabel("DB: 확인 중...")
        self._last_sync_label = QLabel("마지막 동기화: -")

        status_bar.addPermanentWidget(self._connection_label)
        status_bar.addPermanentWidget(self._last_sync_label)

        status_bar.showMessage("애플리케이션이 정상적으로 시작되었습니다.", 5000)
        self.setStatusBar(status_bar)
        self._status_bar = status_bar

        self._init_menu()

    def _init_menu(self) -> None:
        """
        상단 메뉴에 간단한 'AI 요약 테스트' 액션을 추가한다.

        추후에는 Task 상세 화면에서 실제 설명을 요약하는 쪽으로 확장한다.
        """
        menubar = self.menuBar()
        tools_menu = menubar.addMenu("도구")

        ai_test_action = QAction("AI 요약 테스트", self)
        ai_test_action.triggered.connect(self._on_ai_summary_test)  # type: ignore[arg-type]
        tools_menu.addAction(ai_test_action)

    def _init_user_selection(self) -> None:
        """
        사용자 선택 다이얼로그를 표시하고 현재 사용자를 설정한다.
        
        데이터베이스 연결이 실패하면 사용자 선택을 건너뛴다.
        """
        config = load_db_config()
        if config is None:
            QMessageBox.warning(
                self,
                "설정 필요",
                "데이터베이스 설정이 완료되지 않았습니다.\n"
                "환경 변수를 확인한 후 프로그램을 다시 시작하세요.",
            )
            return

        try:
            with db_connection(config) as conn:
                users = list_active_users(conn)
                if not users:
                    QMessageBox.warning(
                        self,
                        "사용자 없음",
                        "활성 사용자가 없습니다.\n데이터베이스를 확인하세요.",
                    )
                    return

                # 사용자 선택 다이얼로그 표시
                dialog = UserSelectionDialog(users, self)
                if dialog.exec_() == QDialog.Accepted:
                    selected_user = dialog.get_selected_user()
                    if selected_user:
                        self._current_user_id = selected_user.id
                        self.setWindowTitle(f"{self._window_title} - {selected_user.display_name}")
                else:
                    # 사용자가 취소한 경우 첫 번째 사용자를 기본값으로 사용
                    self._current_user_id = users[0].id
                    self.setWindowTitle(f"{self._window_title} - {users[0].display_name}")

        except DatabaseConnectionError:
            QMessageBox.warning(
                self,
                "연결 실패",
                "데이터베이스에 연결할 수 없습니다.\n"
                "연결 설정을 확인하세요.",
            )

    def _init_dashboard(self) -> None:
        """
        오른쪽에 간단한 대시보드(내 작업 요약, 기한 임박/지연 목록)를 표시한다.
        """
        dock = QDockWidget("내 작업 요약", self)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)

        widget = QListWidget(dock)
        dock.setWidget(widget)

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self._dashboard_list = widget  # type: ignore[attr-defined]

    def _init_sync(self) -> None:
        """주기적 동기화 타이머를 설정한다."""
        timer = QTimer(self)
        timer.setInterval(5000)  # 5초 간격
        timer.timeout.connect(self._on_sync_timer)  # type: ignore[arg-type]
        timer.start()
        self._sync_timer = timer

    def _set_connection_status(self, ok: bool) -> None:
        if self._connection_label is None:
            return
        if ok:
            self._connection_label.setText("DB: 연결됨")
        else:
            self._connection_label.setText("DB: 끊김")

    def _set_last_sync_time(self, ts: Optional[datetime]) -> None:
        if self._last_sync_label is None:
            return
        if ts is None:
            self._last_sync_label.setText("마지막 동기화: -")
        else:
            text = ts.strftime("마지막 동기화: %Y-%m-%d %H:%M:%S UTC")
            self._last_sync_label.setText(text)

    def _on_sync_timer(self) -> None:
        """
        주기적으로 호출되어 DB 연결 상태와 할 일/알림을 동기화한다.

        UI가 아직 단순하므로, 여기서는:
        - DB 연결 여부만 확인
        - 동기화 시간만 상태바에 반영
        """
        config = load_db_config()
        if config is None:
            self._set_connection_status(False)
            return

        # 사용자가 선택되지 않았으면 동기화 건너뛰기
        if self._current_user_id is None:
            self._set_connection_status(False)
            return

        try:
            with db_connection(config) as conn:
                result, new_state = perform_sync(
                    conn, user_id=self._current_user_id, state=self._sync_state
                )
                self._sync_state = new_state
                self._set_connection_status(True)
                self._set_last_sync_time(result.server_time)
                self._update_dashboard(result.server_time, result.tasks)
        except DatabaseConnectionError:
            self._set_connection_status(False)
        except Exception as exc:
            self._set_connection_status(False)
            QMessageBox.warning(self, "동기화 오류", f"동기화 중 오류가 발생했습니다: {exc}")

    def _update_dashboard(self, now: datetime, tasks) -> None:
        """
        간단한 텍스트 기반 대시보드를 갱신한다.
        """
        widget: Optional[QListWidget] = getattr(self, "_dashboard_list", None)
        if widget is None:
            return

        summary = summarize_tasks(list(tasks), now=now)

        widget.clear()

        widget.addItem(QListWidgetItem(f"전체 작업: {summary.total}"))
        widget.addItem(QListWidgetItem(f"확인 필요: {summary.pending}"))
        widget.addItem(QListWidgetItem(f"확인됨: {summary.confirmed}"))
        widget.addItem(QListWidgetItem(f"진행 중: {summary.in_progress}"))
        widget.addItem(QListWidgetItem(f"검토: {summary.review}"))
        widget.addItem(QListWidgetItem(f"보류: {summary.on_hold}"))
        widget.addItem(QListWidgetItem(f"완료: {summary.completed}"))
        widget.addItem(QListWidgetItem(f"취소: {summary.cancelled}"))
        widget.addItem(QListWidgetItem(f"기한 임박(24h): {summary.due_soon}"))
        widget.addItem(QListWidgetItem(f"기한 초과: {summary.overdue}"))

    def _on_ai_summary_test(self) -> None:
        """
        고정된 예시 텍스트를 이용하여 AI 요약 기능이 동작하는지 테스트한다.

        - AI 설정이 없으면 경고를 띄운다.
        - 호출 실패 시에도 Fallback 설명을 보여준다.
        """
        cfg = load_ai_service_config()
        if cfg is None:
            QMessageBox.information(
                self,
                "AI 설정 필요",
                "AI 요약 서비스를 사용하려면 COLLAB_TODO_AI_BASE_URL 환경 변수를 설정해야 합니다.",
            )
            return

        ai_cfg = AiSummaryConfig(
            base_url=cfg.base_url,
            api_key=cfg.api_key,
            timeout_seconds=cfg.timeout_seconds,
        )

        sample_text = (
            "이 작업은 협업 기반 할 일 관리 시스템의 초기 버전을 구현하는 것입니다. "
            "Windows 데스크톱 클라이언트를 만들고, NAS에 있는 MySQL 데이터베이스와 연동하며, "
            "기본적인 작업 생성, 할당, 완료, 알림 기능을 제공합니다."
        )

        try:
            summary = summarize_text(sample_text, config=ai_cfg, target_language="ko")
        except AiSummaryError as exc:
            QMessageBox.warning(
                self,
                "AI 요약 실패",
                f"요약 서비스 호출에 실패했습니다.\n\n원문:\n{sample_text}\n\n오류: {exc}",
            )
            return

        if not summary:
            summary = "(요약 결과가 비어 있습니다.)"

        QMessageBox.information(
            self,
            "AI 요약 결과",
            f"원문:\n{sample_text}\n\n요약:\n{summary}",
        )


class UserSelectionDialog(QDialog):
    """
    사용자 선택 다이얼로그.
    
    활성 사용자 목록에서 사용자를 선택할 수 있게 한다.
    """

    def __init__(self, users: list[User], parent=None) -> None:
        super().__init__(parent)
        self._users = users
        self._selected_user: Optional[User] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """다이얼로그 UI를 초기화한다."""
        self.setWindowTitle("사용자 선택")
        self.setModal(True)
        self.resize(300, 150)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self._user_combo = QComboBox(self)
        for user in self._users:
            self._user_combo.addItem(f"{user.display_name} ({user.username})", user.id)
        form_layout.addRow("사용자:", self._user_combo)
        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        buttons.accepted.connect(self._on_accept)  # type: ignore[arg-type]
        buttons.rejected.connect(self.reject)  # type: ignore[arg-type]
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        """확인 버튼 클릭 시 선택된 사용자를 저장한다."""
        index = self._user_combo.currentIndex()
        if 0 <= index < len(self._users):
            self._selected_user = self._users[index]
        self.accept()

    def get_selected_user(self) -> Optional[User]:
        """선택된 사용자를 반환한다."""
        return self._selected_user


def main() -> int:
    """
    애플리케이션 진입점.

    - QApplication 인스턴스를 생성한다.
    - MainWindow를 띄운다.
    - 예외 발생 시 비정상 종료 코드를 반환한다.
    """
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    try:
        exit_code = app.exec_()
    except Exception:
        # 초기 단계에서는 예외 메시지를 stdout/stderr에만 남기고
        # 호출자에게 비정상 종료 코드를 전달한다.
        return 1

    return int(exit_code)


if __name__ == "__main__":
    sys.exit(main())


