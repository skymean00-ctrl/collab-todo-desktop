# 설치 프로그램 빌드 문제 해결 가이드

## 일반적인 오류 및 해결 방법

### 오류: "'xxx'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는 배치 파일이 아닙니다."

**원인:**
- 경로에 공백이나 특수문자가 포함됨
- 인코딩 문제
- 명령어가 잘못 파싱됨

**해결 방법:**

1. **간단한 빌드 스크립트 사용**
   ```batch
   build_installer_simple.bat
   ```
   이 스크립트는 더 견고한 경로 처리를 사용합니다.

2. **프로젝트 경로 확인**
   - 프로젝트 폴더 경로에 한글이나 특수문자가 있는지 확인
   - 가능하면 영문 경로 사용 (예: `C:\Projects\collab-todo-desktop`)

3. **관리자 권한으로 실행**
   - 명령 프롬프트를 관리자 권한으로 실행
   - 빌드 스크립트 실행

### 오류: "Python을 찾을 수 없습니다"

**해결 방법:**

1. Python이 설치되어 있는지 확인:
   ```batch
   python --version
   ```

2. PATH 환경 변수에 Python이 추가되어 있는지 확인

3. Python 설치 시 "Add Python to PATH" 옵션을 체크했는지 확인

4. 수동으로 PATH 추가:
   - 시스템 속성 → 환경 변수
   - PATH에 Python 설치 경로 추가 (예: `C:\Python311`)

### 오류: "Inno Setup을 찾을 수 없습니다"

**해결 방법:**

1. Inno Setup 6 설치 확인:
   - https://jrsoftware.org/isdl.php 에서 다운로드
   - 설치 완료 확인

2. 설치 경로 확인:
   - 기본 경로: `C:\Program Files (x86)\Inno Setup 6\`
   - 또는: `C:\Program Files\Inno Setup 6\`

3. 수동으로 경로 지정:
   ```batch
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```

### 오류: "PyInstaller 빌드 실패"

**해결 방법:**

1. 의존성 설치 확인:
   ```batch
   pip install -r requirements.txt
   ```

2. PyInstaller 재설치:
   ```batch
   pip uninstall pyinstaller
   pip install pyinstaller==6.11.1
   ```

3. 가상환경 사용:
   ```batch
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

### 오류: "빌드된 실행 파일을 찾을 수 없습니다"

**해결 방법:**

1. `dist` 디렉토리 확인:
   ```batch
   dir dist
   ```

2. 빌드 로그 확인:
   - `build` 디렉토리의 로그 파일 확인
   - 오류 메시지 확인

3. 수동 빌드 시도:
   ```batch
   pyinstaller pyinstaller.spec --clean --noconfirm
   ```

## 단계별 수동 빌드

빌드 스크립트가 작동하지 않으면 다음 단계를 수동으로 실행하세요:

### 1단계: 환경 준비

```batch
REM 프로젝트 디렉토리로 이동
cd C:\path\to\collab-todo-desktop

REM 가상환경 활성화
.venv\Scripts\activate

REM 의존성 설치
pip install -r requirements.txt
```

### 2단계: PyInstaller 빌드

```batch
REM 기존 빌드 정리
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 실행 파일 빌드
pyinstaller pyinstaller.spec --clean --noconfirm
```

### 3단계: Inno Setup 컴파일

```batch
REM Inno Setup 컴파일러 실행
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

또는 Inno Setup Compiler GUI에서:
1. Inno Setup Compiler 실행
2. `installer.iss` 파일 열기
3. Build → Compile 클릭

## 인코딩 문제 해결

한글 경로나 파일명으로 인한 문제:

1. **프로젝트를 영문 경로로 이동**
   ```
   C:\Projects\collab-todo-desktop
   ```

2. **명령 프롬프트 인코딩 설정**
   ```batch
   chcp 65001
   ```

3. **UTF-8 BOM 없는 스크립트 사용**
   - `build_installer_simple.bat` 사용

## 추가 도움말

### 로그 확인

빌드 실패 시 다음 로그 확인:
- PyInstaller 로그: `build\CollabToDoDesktop\warn-CollabToDoDesktop.txt`
- Inno Setup 로그: 컴파일 창의 오류 메시지

### 시스템 요구사항 확인

- Windows 10 이상
- Python 3.11+
- 최소 2GB RAM
- 최소 500MB 디스크 공간

### 지원

문제가 계속되면:
1. 전체 오류 메시지 복사
2. 빌드 로그 파일 확인
3. 시스템 정보 확인 (Python 버전, Windows 버전)

---

**마지막 업데이트**: 2025-01-XX

