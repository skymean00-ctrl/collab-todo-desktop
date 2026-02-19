# collab-todo-desktop

Windows용 협업 워크플로우 할 일 관리 데스크톱 클라이언트입니다.

팀 내에서 업무를 생성하고, 담당자를 지정하며, 진행 상태를 실시간으로 추적할 수 있습니다. NAS 환경의 MySQL 데이터베이스와 연동하여 사내 네트워크에서 별도 클라우드 서비스 없이 운영됩니다.

## 주요 기능

- **업무 관리** - 프로젝트별 업무 생성/수정/삭제, 하위 업무(subtask) 지원
- **업무 흐름** - 대기 → 확인 → 진행 중 → 검토 → 완료 (보류/취소 포함)
- **담당자 지정** - 사용자별 업무 할당, 다음 담당자 위임
- **실시간 동기화** - 5초 간격 자동 동기화로 팀원 간 최신 상태 유지
- **알림 시스템** - 업무 할당/상태 변경 시 실시간 알림
- **대시보드** - 내 작업 요약 (상태별 개수, 기한 임박/초과 표시)
- **파일 첨부** - 업무별 파일 첨부 기능
- **공개/비공개 업무** - 비공개 업무에 대한 열람 권한 관리
- **사용자 관리** - 관리자 전용 사용자 등록/관리/역할 설정
- **AI 요약** - 외부 AI 서비스 연동을 통한 업무 내용 요약 (선택사항)

## 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| UI 프레임워크 | PyQt5 |
| 데이터베이스 | MySQL (NAS 환경) |
| 패키징 | PyInstaller + Inno Setup |
| 테스트 | pytest |

## 빠른 시작

### 원격에서 자동 빌드 (권장)

`build_from_scratch.bat` 파일 하나만 다운로드하여 실행하면 자동으로 프로젝트를 다운로드하고 빌드합니다.

자세한 내용은 [QUICK_START.md](QUICK_START.md) 참조.

## 설치 프로그램 빌드

### 사전 요구사항

1. **Python 3.11+** 및 가상환경
2. **PyInstaller 6.11.1** (requirements.txt에 포함)
3. **Inno Setup 6** ([다운로드](https://jrsoftware.org/isdl.php))

### 빌드 방법

#### 방법 1: 원격 자동 다운로드 및 빌드 (가장 간단)

```batch
build_from_scratch.bat
```

이 스크립트는 GitHub에서 프로젝트를 자동으로 다운로드하고 빌드합니다.

#### 방법 2: 전체 프로젝트가 있는 경우

```batch
# 1. 가상환경 활성화
.venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 설치 프로그램 빌드
build_installer_complete.bat
```

빌드된 설치 프로그램은 `installer\CollabTodoDesktop-Setup-1.0.0.exe`에 생성됩니다.

#### Linux/macOS에서 빌드 (WINE 필요)

```bash
# 1. 가상환경 활성화
source .venv/bin/activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 설치 프로그램 빌드 (WINE 필요)
chmod +x build_installer.sh
./build_installer.sh
```

### 설치 프로그램 포함 내용

- Python 런타임 포함 (사용자가 Python을 설치할 필요 없음)
- 모든 애플리케이션 바이너리 및 의존성
- 시작 메뉴 및 바탕화면 바로가기
- 제거 프로그램 (Uninstaller)
- 설정 가이드 문서

### 사용자 설치 가이드

사용자는 `docs/INSTALLATION_GUIDE.md`를 참조하여 프로그램을 설치하고 설정할 수 있습니다.

## 환경 설정

`config/env.example`을 참고하여 시스템 환경 변수를 설정합니다.

```bash
# 데이터베이스 연결 (필수)
COLLAB_TODO_DB_HOST=192.168.1.100
COLLAB_TODO_DB_PORT=3306
COLLAB_TODO_DB_USER=your_username
COLLAB_TODO_DB_PASSWORD=your_password
COLLAB_TODO_DB_NAME=collab_todo

# AI 요약 서비스 (선택사항)
COLLAB_TODO_AI_BASE_URL=https://your-ai-service-url/api
COLLAB_TODO_AI_API_KEY=your-api-key-here
```

## 개발

### 로컬 실행

```bash
# 가상환경 활성화
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# 의존성 설치
pip install -r requirements.txt

# 실행
python main.py
```

### 테스트

```bash
pytest tests/
```

### 데이터베이스 초기화

```bash
# 1. 초기 스키마 생성
mysql -u root -p collab_todo < sql/schema_mysql.sql

# 2. v2 마이그레이션 적용 (하위업무, 첨부파일, 공개/비공개 등)
mysql -u root -p collab_todo < sql/migration_v2.sql
```

## 프로젝트 구조

```
collab-todo-desktop/
├── collab_todo/                # 메인 애플리케이션 패키지
│   ├── ui/                     # PyQt5 UI 위젯
│   │   ├── login_dialog.py     #   로그인 다이얼로그
│   │   ├── register_dialog.py  #   회원가입 다이얼로그
│   │   ├── task_list_widget.py #   업무 목록
│   │   ├── task_detail_widget.py #  업무 상세
│   │   ├── create_task_dialog.py #  업무 생성
│   │   ├── notification_widget.py # 알림 패널
│   │   ├── attachment_widget.py #   파일 첨부
│   │   └── user_management_widget.py # 사용자 관리
│   ├── models/                 # 데이터 모델 (User, Task, Project 등)
│   ├── repositories/           # DB 접근 계층 (CRUD)
│   ├── services/               # 비즈니스 로직 (인증 등)
│   ├── config.py               # 환경 변수 기반 설정 로드
│   ├── db.py                   # DB 연결 관리
│   ├── sync.py                 # 실시간 동기화
│   ├── dashboard.py            # 작업 요약 통계
│   ├── notifications.py        # 알림 처리
│   ├── ai_client.py            # AI 요약 서비스 연동
│   └── session.py              # 사용자 세션 관리
├── tests/                      # 테스트 코드
├── tools/                      # 개발 유틸리티 스크립트
├── sql/                        # DB 스키마 및 마이그레이션
├── docs/                       # 문서
├── config/                     # 설정 파일 예제
├── main.py                     # 애플리케이션 진입점
├── pyinstaller.spec            # PyInstaller 설정
├── installer.iss               # Inno Setup 스크립트
├── build_installer.bat         # Windows 빌드 스크립트
├── build_installer_complete.bat # 완전 자동 빌드 스크립트
├── build_installer_simple.bat  # 간단한 빌드 스크립트
├── build_installer.sh          # Linux/macOS 빌드 스크립트
└── build_from_scratch.bat      # 원격 자동 다운로드 및 빌드
```

## 문서

- [QUICK_START.md](QUICK_START.md) - 빠른 시작 가이드
- [README_BUILD.md](README_BUILD.md) - 빌드 방법 상세 가이드
- [BUILD_INSTALLER.md](BUILD_INSTALLER.md) - 설치 프로그램 빌드 가이드
- [DEPLOYMENT.md](DEPLOYMENT.md) - 배포 가이드
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 문제 해결 가이드
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - 개선 사항 내역

## 라이선스

[라이선스 정보 추가]
