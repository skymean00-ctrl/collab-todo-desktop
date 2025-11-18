collab-todo-desktop
====================

Windows용 협업 워크플로우 할 일 관리 프로그램의 데스크톱 클라이언트입니다.

현재 단계(v1.0 Phase 1) 목표:
- Python + PyQt5 기반 단일 실행 파일/설치 프로그램 배포
- NAS 상의 MySQL/PostgreSQL 데이터베이스와 연동
- 기본 사용자/프로젝트/작업(Task) 보기
- 네트워크 연결 상태 표시

차후 단계에서 순차 위임, 알림, 이력, AI 요약 기능을 추가합니다.

## 설치 프로그램 빌드

### 사전 요구사항

1. **Python 3.11+** 및 가상환경
2. **PyInstaller 6.11.1** (requirements.txt에 포함)
3. **Inno Setup 6** ([다운로드](https://jrsoftware.org/isdl.php))

### 빌드 방법

#### Windows에서 빌드

```batch
# 1. 가상환경 활성화
.venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 설치 프로그램 빌드
build_installer.bat
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

- ✅ 모든 애플리케이션 바이너리 및 의존성
- ✅ 시작 메뉴 바로가기
- ✅ 바탕화면 바로가기 (선택적)
- ✅ 제거 프로그램 (Uninstaller)
- ✅ 설정 가이드 문서 (`docs\INSTALLATION_GUIDE.md`)

### 사용자 설치 가이드

사용자는 `docs\INSTALLATION_GUIDE.md`를 참조하여 프로그램을 설치하고 설정할 수 있습니다.

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

## 프로젝트 구조

```
collab-todo-desktop/
├── collab_todo/          # 메인 애플리케이션 코드
├── tests/                # 테스트 코드
├── sql/                  # 데이터베이스 스키마
├── docs/                 # 문서 (설치 가이드 등)
├── config/               # 설정 파일 예제
├── installer/            # 빌드된 설치 프로그램 출력 디렉토리
├── main.py              # 애플리케이션 진입점
├── pyinstaller.spec     # PyInstaller 설정
├── installer.iss        # Inno Setup 스크립트
├── build_installer.bat  # Windows 빌드 스크립트
└── build_installer.sh   # Linux/macOS 빌드 스크립트 (WINE)
```

## 라이선스

[라이선스 정보 추가]

