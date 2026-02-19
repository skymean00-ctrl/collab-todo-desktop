# PyInstaller spec file for collab-todo-desktop
# 독립 실행형 Windows 설치 파일 생성을 위한 설정
# Python 런타임 및 모든 의존성이 포함됩니다.

block_cipher = None


def get_datas():
    """
    추가 데이터 파일 목록.
    향후 아이콘, 번역 파일, 설정 템플릿 등을 추가할 수 있습니다.
    """
    datas = []
    
    # 설정 파일 예제 포함
    try:
        import os
        config_example = 'config/env.example'
        if os.path.exists(config_example):
            datas.append((config_example, 'config'))
    except:
        pass
    
    return datas


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=get_datas(),
    hiddenimports=[
        # PyQt5 모듈
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        # MySQL 커넥터 (모든 하위 모듈 포함 - 누락 시 런타임 에러)
        'mysql.connector',
        'mysql.connector.connection',
        'mysql.connector.connection_cext',
        'mysql.connector.cursor',
        'mysql.connector.cursor_cext',
        'mysql.connector.errorcode',
        'mysql.connector.errors',
        'mysql.connector.plugins',
        'mysql.connector.plugins.mysql_native_password',
        'mysql.connector.plugins.caching_sha2_password',
        'mysql.connector.plugins.sha256_password',
        # Requests 및 의존성
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        # collab_todo 패키지 전체 (동적 import 누락 방지)
        'collab_todo',
        'collab_todo.config',
        'collab_todo.db',
        'collab_todo.sync',
        'collab_todo.dashboard',
        'collab_todo.ai_client',
        'collab_todo.session',
        'collab_todo.notifications',
        'collab_todo.models',
        'collab_todo.models.user',
        'collab_todo.models.project',
        'collab_todo.models.task',
        'collab_todo.models.task_attachment',
        'collab_todo.models.task_history',
        'collab_todo.models.notification',
        'collab_todo.repositories',
        'collab_todo.repositories.user_repo',
        'collab_todo.repositories.project_repo',
        'collab_todo.repositories.task_repo',
        'collab_todo.repositories.attachment_repo',
        'collab_todo.repositories.history_repo',
        'collab_todo.repositories.notification_repo',
        'collab_todo.repositories.subtask_repo',
        'collab_todo.repositories.viewer_repo',
        'collab_todo.services',
        'collab_todo.services.auth_service',
        'collab_todo.ui',
        'collab_todo.ui.login_dialog',
        'collab_todo.ui.register_dialog',
        'collab_todo.ui.task_list_widget',
        'collab_todo.ui.task_detail_widget',
        'collab_todo.ui.create_task_dialog',
        'collab_todo.ui.notification_widget',
        'collab_todo.ui.attachment_widget',
        'collab_todo.ui.user_management_widget',
        # 기타 필수 모듈
        'datetime',
        'typing',
        'dataclasses',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 불필요한 모듈 제외 (용량 최적화)
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 단일 실행 파일로 빌드 (모든 의존성 포함)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CollabToDoDesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # UPX 압축 사용 (파일 크기 감소)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 콘솔 창 숨김 (GUI 앱)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # 자동 감지 (64비트 우선)
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 향후 아이콘 파일 경로 지정 가능
    version=None,  # 향후 버전 정보 파일 지정 가능
)


