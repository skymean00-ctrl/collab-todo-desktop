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
)
from PyQt5.QtCore import Qt, QTimer

from collab_todo.config import load_db_config, load_ai_service_config
from collab_todo.db import db_connection, DatabaseConnectionError
from collab_todo.sync import SyncState, perform_sync
from collab_todo.dashboard import summarize_tasks
from collab_todo.ai_client import AiSummaryConfig, summarize_text, AiSummaryError
from collab_todo.models import User
from collab_todo.session import Session
from collab_todo.ui.login_dialog import LoginDialog
from collab_todo.ui.register_dialog import RegisterDialog
from collab_todo.ui.user_management_widget import UserManagementWidget
from collab_todo.ui.task_list_widget import TaskListWidget
from collab_todo.ui.task_detail_widget import TaskDetailWidget
from collab_todo.ui.create_task_dialog import CreateTaskDialog
from collab_todo.ui.notification_widget import NotificationWidget
from collab_todo.ui.attachment_widget import AttachmentWidget


class MainWindow(QMainWindow):
    """
    애플리케이션의 기본 메인 창.

    로그인 성공 후 메인 화면을 표시한다.
    """

    def __init__(
        self,
        *,
        session: Session,
        window_title: str = "Collab To-Do Desktop",
    ) -> None:
        super().__init__()

        self._window_title: str = window_title
        self._session: Session = session
        self._status_bar: Optional[QStatusBar] = None
        self._last_sync_label: Optional[QLabel] = None
        self._connection_label: Optional[QLabel] = None
        self._user_label: Optional[QLabel] = None
        self._sync_timer: Optional[QTimer] = None
        self._sync_state: SyncState = SyncState(last_synced_at=None)

        self._user_map: dict[int, str] = {}

        self._init_ui()
        self._init_task_panels()
        self._init_sync()
        self._init_dashboard()
        self._init_notification_panel()
        self._load_user_map()

    @property
    def _current_user_id(self) -> Optional[int]:
        return self._session.user_id if self._session.is_logged_in else None

    def _init_ui(self) -> None:
        """기본 UI 구성 요소를 초기화한다."""
        self.setWindowTitle(
            f"{self._window_title} - {self._session.display_name}"
        )
        self.resize(1024, 640)

        status_bar = QStatusBar(self)
        self._connection_label = QLabel("DB: 확인 중...")
        self._last_sync_label = QLabel("마지막 동기화: -")
        self._user_label = QLabel(f"사용자: {self._session.display_name}")

        status_bar.addPermanentWidget(self._user_label)
        status_bar.addPermanentWidget(self._connection_label)
        status_bar.addPermanentWidget(self._last_sync_label)

        status_bar.showMessage("애플리케이션이 정상적으로 시작되었습니다.", 5000)
        self.setStatusBar(status_bar)
        self._status_bar = status_bar

        self._init_menu()

    def _init_menu(self) -> None:
        menubar = self.menuBar()

        # 도구 메뉴
        tools_menu = menubar.addMenu("도구")

        ai_test_action = QAction("AI 요약 테스트", self)
        ai_test_action.triggered.connect(self._on_ai_summary_test)
        tools_menu.addAction(ai_test_action)

        # 관리자 메뉴 (admin만 보임)
        if self._session.is_admin:
            admin_menu = menubar.addMenu("관리")

            user_mgmt_action = QAction("사용자 관리", self)
            user_mgmt_action.triggered.connect(self._on_user_management)
            admin_menu.addAction(user_mgmt_action)

        # 계정 메뉴
        account_menu = menubar.addMenu("계정")

        logout_action = QAction("로그아웃", self)
        logout_action.triggered.connect(self._on_logout)
        account_menu.addAction(logout_action)

    def _init_task_panels(self) -> None:
        """업무 목록(좌측) + 상세(중앙) 패널 구성."""
        from PyQt5.QtWidgets import QSplitter

        splitter = QSplitter(Qt.Horizontal, self)

        # 좌측: 업무 목록
        self._task_list = TaskListWidget()
        self._task_list.task_selected.connect(self._on_task_selected)
        self._task_list.create_requested.connect(self._on_create_task)
        self._task_list.view_combo.currentIndexChanged.connect(
            lambda _: self._refresh_task_list()
        )
        splitter.addWidget(self._task_list)

        # 우측: 업무 상세
        self._task_detail = TaskDetailWidget(
            current_user_id=self._session.user_id
        )
        self._task_detail.task_updated.connect(self._refresh_task_list)
        splitter.addWidget(self._task_detail)

        splitter.setSizes([400, 600])
        self.setCentralWidget(splitter)

    def _load_user_map(self) -> None:
        """활성 사용자 ID→이름 맵 로드."""
        from collab_todo.repositories import list_active_users

        config = load_db_config()
        if config is None:
            return
        try:
            with db_connection(config) as conn:
                users = list_active_users(conn)
                self._user_map = {u.id: u.display_name for u in users}
                self._task_detail.set_user_map(self._user_map)
        except DatabaseConnectionError:
            pass

    def _refresh_task_list(self) -> None:
        """현재 뷰에 맞게 업무 목록을 새로고침한다."""
        from collab_todo.repositories import list_tasks_for_assignee, list_tasks_created_by_user

        config = load_db_config()
        if config is None or self._current_user_id is None:
            return

        try:
            with db_connection(config) as conn:
                if self._task_list.current_view == "assignee":
                    tasks = list_tasks_for_assignee(conn, self._current_user_id)
                else:
                    tasks = list_tasks_created_by_user(conn, self._current_user_id)

                self._task_list.set_tasks(tasks, self._user_map)
        except DatabaseConnectionError:
            pass

    def _on_task_selected(self, task) -> None:
        self._task_detail.show_task(task)

    def _on_create_task(self) -> None:
        """새 업무 생성 다이얼로그."""
        from collab_todo.repositories import list_active_users, list_projects_for_user, create_task

        config = load_db_config()
        if config is None or self._session.user is None:
            return

        try:
            with db_connection(config) as conn:
                users = list_active_users(conn)
                projects = list_projects_for_user(conn, self._session.user_id)

                if not projects:
                    QMessageBox.information(
                        self, "프로젝트 필요", "먼저 프로젝트를 생성하세요."
                    )
                    return

                dialog = CreateTaskDialog(
                    current_user=self._session.user,
                    users=users,
                    projects=projects,
                    parent=self,
                )

                if dialog.exec_() == QDialog.Accepted:
                    data = dialog.get_task_data()
                    if data is not None:
                        create_task(conn, **data)
                        conn.commit()
                        self._refresh_task_list()

        except DatabaseConnectionError:
            QMessageBox.warning(self, "오류", "DB 연결에 실패했습니다.")

    def _init_dashboard(self) -> None:
        dock = QDockWidget("내 작업 요약", self)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)

        widget = QListWidget(dock)
        dock.setWidget(widget)

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self._dashboard_list = widget

    def _init_notification_panel(self) -> None:
        """알림 패널을 우측 하단에 도킹."""
        self._notification_widget = NotificationWidget(
            user_id=self._session.user_id
        )

        dock = QDockWidget("알림", self)
        dock.setWidget(self._notification_widget)
        dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def _init_sync(self) -> None:
        timer = QTimer(self)
        timer.setInterval(5000)
        timer.timeout.connect(self._on_sync_timer)
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
        config = load_db_config()
        if config is None:
            self._set_connection_status(False)
            return

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
                self._task_list.set_tasks(result.tasks, self._user_map)
                self._notification_widget.set_notifications(result.notifications)
        except DatabaseConnectionError:
            self._set_connection_status(False)
        except Exception as exc:
            self._set_connection_status(False)
            QMessageBox.warning(self, "동기화 오류", f"동기화 중 오류가 발생했습니다: {exc}")

    def _update_dashboard(self, now: datetime, tasks) -> None:
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

    def _on_user_management(self) -> None:
        """관리자 전용: 사용자 관리 패널을 띄운다."""
        widget = UserManagementWidget(self)
        widget.refresh()

        dock = QDockWidget("사용자 관리", self)
        dock.setWidget(widget)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _on_logout(self) -> None:
        """로그아웃: 세션 초기화 후 창 닫기."""
        self._session.logout()
        if self._sync_timer:
            self._sync_timer.stop()
        self.close()


def _show_login_flow(app: QApplication) -> Optional[Session]:
    """로그인/가입 플로우를 처리하고 세션을 반환한다."""
    session = Session()

    while True:
        login_dialog = LoginDialog()

        register_requested = [False]

        def on_register():
            register_requested[0] = True

        login_dialog.register_requested.connect(on_register)

        result = login_dialog.exec_()

        if result == QDialog.Accepted:
            user = login_dialog.get_logged_in_user()
            if user is not None:
                session.login(user)
                return session

        if register_requested[0]:
            reg_dialog = RegisterDialog()
            reg_dialog.exec_()
            continue

        # 사용자가 로그인을 취소
        return None


def main() -> int:
    """
    애플리케이션 진입점.

    로그인 → 메인 화면 순서로 진행한다.
    로그아웃 시 다시 로그인 화면으로 돌아간다.
    """
    app = QApplication(sys.argv)

    while True:
        session = _show_login_flow(app)
        if session is None:
            return 0

        window = MainWindow(session=session)
        window.show()

        try:
            exit_code = app.exec_()
        except Exception:
            return 1

        # 로그아웃으로 창이 닫힌 경우 → 다시 로그인 화면
        if not session.is_logged_in:
            continue

        return int(exit_code)


if __name__ == "__main__":
    sys.exit(main())
