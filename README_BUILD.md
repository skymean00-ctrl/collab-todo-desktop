# 설치 프로그램 빌드 방법

## 방법 1: 전체 프로젝트가 있는 경우 (개발자용)

프로젝트 폴더가 이미 있는 경우:

```batch
build_installer_complete.bat
```

또는

```batch
build_installer_simple.bat
```

## 방법 2: 원격에서 자동 다운로드 및 빌드 (권장) ⭐

**이 방법은 `build_from_scratch.bat` 파일 하나만 있으면 됩니다!**

### 사용 방법

1. **`build_from_scratch.bat` 파일만 다운로드**
   - GitHub 저장소에서 이 파일만 다운로드
   - 또는 이 파일을 어디든 복사

2. **Windows에서 실행**
   ```batch
   build_from_scratch.bat
   ```

3. **자동으로 수행되는 작업:**
   - ✅ GitHub에서 프로젝트 자동 다운로드
   - ✅ Python 가상환경 자동 생성
   - ✅ 모든 의존성 자동 설치
   - ✅ 실행 파일 자동 빌드
   - ✅ 설치 프로그램 자동 생성

### 필요 사항

- **Python 3.11+** (설치되어 있어야 함)
- **인터넷 연결** (프로젝트 다운로드용)
- **Inno Setup 6** (선택적, 없어도 실행 파일은 생성됨)

### GitHub 저장소 설정

`build_from_scratch.bat` 파일에서 다음을 수정하세요:

```batch
set "GITHUB_REPO=https://github.com/your-org/collab-todo-desktop.git"
set "GITHUB_ZIP=https://github.com/your-org/collab-todo-desktop/archive/main.zip"
```

실제 GitHub 저장소 URL로 변경하세요.

### 작동 방식

1. **Git이 있는 경우:**
   - `git clone`을 사용하여 프로젝트 다운로드

2. **Git이 없는 경우:**
   - PowerShell을 사용하여 ZIP 파일 다운로드
   - 자동으로 압축 해제

3. **빌드 진행:**
   - 기존 빌드 스크립트와 동일하게 진행

## 방법 3: 수동 다운로드 후 빌드

1. **프로젝트 다운로드**
   - GitHub에서 ZIP 파일 다운로드
   - 압축 해제

2. **빌드 스크립트 실행**
   ```batch
   cd collab-todo-desktop
   build_installer_complete.bat
   ```

## 결과

모든 방법의 결과는 동일합니다:

```
installer\CollabTodoDesktop-Setup-1.0.0.exe
```

이 파일을 사용자에게 배포하면 됩니다.

## 문제 해결

### "Python을 찾을 수 없습니다"

- Python 3.11 이상 설치 필요
- 설치 시 "Add Python to PATH" 옵션 체크

### "프로젝트 다운로드 실패"

- 인터넷 연결 확인
- GitHub 저장소 URL 확인
- 방화벽 설정 확인

### "Inno Setup을 찾을 수 없습니다"

- Inno Setup 6 설치: https://jrsoftware.org/isdl.php
- 없어도 실행 파일(`dist\CollabToDoDesktop.exe`)은 생성됨

자세한 내용은 `TROUBLESHOOTING.md` 참조.

