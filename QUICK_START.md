# 빠른 시작 가이드

## 🚀 가장 간단한 방법: 원격 자동 빌드

### 1단계: 파일 하나만 다운로드

`build_from_scratch.bat` 파일만 다운로드하세요.

### 2단계: 실행

Windows에서 더블클릭하거나 명령 프롬프트에서 실행:

```batch
build_from_scratch.bat
```

### 3단계: 완료!

스크립트가 자동으로:
- ✅ 프로젝트 다운로드
- ✅ 환경 설정
- ✅ 빌드
- ✅ 설치 프로그램 생성

결과: `collab-todo-desktop\installer\CollabTodoDesktop-Setup-1.0.0.exe`

---

## 📋 사전 요구사항

### 필수
- **Windows 10 이상**
- **Python 3.11+** ([다운로드](https://www.python.org/downloads/))
  - 설치 시 **"Add Python to PATH"** 체크 필수!
- **인터넷 연결**

### 선택적
- **Git** (있으면 더 빠름, 없어도 됨)
- **Inno Setup 6** (설치 프로그램 생성용, 없어도 실행 파일은 생성됨)

---

## ⚙️ GitHub 저장소 설정

`build_from_scratch.bat` 파일을 열어서 다음 줄을 수정하세요:

```batch
set "GITHUB_REPO=https://github.com/your-username/collab-todo-desktop.git"
set "GITHUB_ZIP=https://github.com/your-username/collab-todo-desktop/archive/main.zip"
```

실제 GitHub 저장소 URL로 변경하세요.

### GitHub 저장소가 없는 경우

1. **프로젝트를 ZIP으로 압축**
2. **웹 서버나 파일 공유 서비스에 업로드**
3. **`build_from_scratch.bat`에서 ZIP URL 수정:**

```batch
set "GITHUB_ZIP=https://your-server.com/collab-todo-desktop.zip"
```

---

## 🔧 다른 방법들

### 방법 A: 전체 프로젝트가 있는 경우

프로젝트 폴더가 이미 있다면:

```batch
build_installer_complete.bat
```

### 방법 B: 수동 다운로드

1. GitHub에서 프로젝트 ZIP 다운로드
2. 압축 해제
3. `build_installer_complete.bat` 실행

---

## ❓ 문제 해결

### Python을 찾을 수 없습니다

**해결:**
1. Python 설치 확인: `python --version`
2. PATH 환경 변수에 Python 추가
3. Python 재설치 시 "Add Python to PATH" 체크

### 다운로드 실패

**해결:**
1. 인터넷 연결 확인
2. GitHub 저장소 URL 확인
3. 방화벽/프록시 설정 확인
4. 수동으로 ZIP 다운로드 후 압축 해제

### 빌드 실패

**해결:**
- `TROUBLESHOOTING.md` 참조
- 로그 파일 확인
- Python 버전 확인 (3.11+ 필요)

---

## 📦 결과물

빌드 성공 시:

```
collab-todo-desktop\
  └── installer\
      └── CollabTodoDesktop-Setup-1.0.0.exe  ← 이것을 배포!
```

이 파일 하나만 사용자에게 배포하면 됩니다!

---

## 💡 팁

1. **첫 실행은 시간이 걸립니다** (다운로드 + 빌드)
2. **인터넷 연결이 안정적이어야 합니다**
3. **디스크 공간이 충분한지 확인** (최소 1GB 권장)
4. **바이러스 백신이 차단할 수 있습니다** (예외 추가)

---

**더 자세한 내용은 `README_BUILD.md` 참조**

