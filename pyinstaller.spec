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
        # MySQL 커넥터
        'mysql.connector',
        'mysql.connector.connection',
        'mysql.connector.cursor',
        # Requests 및 의존성
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
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


