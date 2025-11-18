# Windows 설치 프로그램 빌드 가이드

## 중요: 독립 실행형 설치 파일

이 설치 프로그램은 **모든 의존성을 포함**합니다:
- ✅ **Python 런타임 포함** - 사용자가 Python을 설치할 필요 없음
- ✅ **모든 라이브러리 포함** - PyQt5, mysql-connector 등 자동 포함
- ✅ **단일 설치 파일** - 하나의 .exe 파일로 모든 것을 설치
- ✅ **추가 설치 불필요** - 설치 후 즉시 사용 가능

**사용자는 이 설치 파일만 실행하면 됩니다. 별도의 Python 설치나 라이브러리 설치가 필요하지 않습니다.**

## 현재 상태

설치 파일(`CollabTodoDesktop-Setup-1.0.0.exe`)은 아직 빌드되지 않았습니다.
Windows 환경에서 다음 단계를 따라 빌드하세요.

## 사전 요구사항

### 1. Python 3.11+ 설치
- [Python 공식 사이트](https://www.python.org/downloads/)에서 다운로드
- 설치 시 "Add Python to PATH" 옵션 체크

### 2. Inno Setup 6 설치
- [Inno Setup 다운로드](https://jrsoftware.org/isdl.php)
- 기본 경로로 설치:
  - `C:\Program Files (x86)\Inno Setup 6\` 또는
  - `C:\Program Files\Inno Setup 6\`

### 3. 프로젝트 의존성 설치

프로젝트 디렉토리에서:

```batch
# 가상환경 생성 (아직 없다면)
python -m venv .venv

# 가상환경 활성화
.venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

## 빌드 방법

### 방법 1: 완전 자동 빌드 스크립트 사용 (가장 권장) ⭐

```batch
# 프로젝트 디렉토리에서
build_installer_complete.bat
```

이 스크립트가 자동으로:
1. 가상환경 확인 및 생성 (없는 경우)
2. 모든 의존성 설치
3. PyInstaller로 실행 파일 빌드 (Python 런타임 포함)
4. Inno Setup으로 설치 프로그램 생성
5. 빌드 결과 확인 및 안내

**가장 간단하고 안전한 방법입니다.**

### 방법 2: 기본 빌드 스크립트 사용

```batch
# 프로젝트 디렉토리에서
build_installer.bat
```

이 스크립트가 자동으로:
1. PyInstaller로 실행 파일 빌드
2. Inno Setup으로 설치 프로그램 생성

### 방법 2: 수동 빌드

#### 1단계: PyInstaller로 실행 파일 빌드

```batch
# 가상환경 활성화
.venv\Scripts\activate

# 실행 파일 빌드
pyinstaller pyinstaller.spec --clean --noconfirm
```

빌드된 파일: `dist\CollabToDoDesktop.exe`

#### 2단계: Inno Setup으로 설치 프로그램 생성

1. Inno Setup Compiler 실행
2. `installer.iss` 파일 열기
3. **Build** → **Compile** 클릭

또는 명령줄에서:

```batch
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

## 빌드 결과

빌드가 성공하면 다음 위치에 설치 파일이 생성됩니다:

```
installer\CollabTodoDesktop-Setup-1.0.0.exe
```

## 문제 해결

### Inno Setup을 찾을 수 없습니다

**해결 방법**:
1. Inno Setup이 설치되어 있는지 확인
2. 설치 경로 확인:
   - `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
   - `C:\Program Files\Inno Setup 6\ISCC.exe`
3. `build_installer.bat` 파일에서 경로 수정

### PyInstaller 빌드 실패

**해결 방법**:
1. 모든 의존성이 설치되었는지 확인:
   ```batch
   pip install -r requirements.txt
   ```
2. Python 버전 확인 (3.11+ 필요)
3. 가상환경이 활성화되었는지 확인

### 실행 파일이 생성되지 않습니다

**해결 방법**:
1. `dist` 디렉토리 확인
2. 빌드 로그에서 오류 메시지 확인
3. PyInstaller 버전 확인:
   ```batch
   pip show pyinstaller
   ```

## 설치 프로그램 테스트

빌드된 설치 프로그램을 테스트하려면:

1. `installer\CollabTodoDesktop-Setup-1.0.0.exe` 실행
2. 설치 마법사가 정상적으로 작동하는지 확인
3. 설치 후 프로그램이 정상 실행되는지 확인
4. 제거 프로그램이 정상 작동하는지 확인

## 배포

빌드된 설치 파일을 배포하려면:

1. `installer\CollabTodoDesktop-Setup-1.0.0.exe` 파일을 사용자에게 제공
2. 사용자는 이 파일을 실행하여 설치
3. 설치 가이드는 `docs\INSTALLATION_GUIDE.md` 참조

---

**참고**: 현재 Linux 환경에서는 Windows 설치 프로그램을 직접 빌드할 수 없습니다. 
Windows 환경에서 위의 단계를 따라 빌드하세요.

