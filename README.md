# collab-todo-desktop

Windows용 협업 워크플로우 할 일 관리 프로그램의 데스크톱 클라이언트입니다.

현재 단계(v1.0 Phase 1) 목표:
- Python + PyQt5 기반 단일 실행 파일/설치 프로그램 배포
- NAS 상의 MySQL/PostgreSQL 데이터베이스와 연동
- 기본 사용자/프로젝트/작업(Task) 보기
- 네트워크 연결 상태 표시

차후 단계에서 순차 위임, 알림, 이력, AI 요약 기능을 추가합니다.

## 빠른 시작

### 원격에서 자동 빌드 (권장) ⭐

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

- ✅ **Python 런타임 포함** - 사용자가 Python을 설치할 필요 없음
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
├── build_installer_complete.bat  # 완전 자동 빌드 스크립트
├── build_installer_simple.bat    # 간단한 빌드 스크립트
└── build_from_scratch.bat         # 원격 자동 다운로드 및 빌드
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
