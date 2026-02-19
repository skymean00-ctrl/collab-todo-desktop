# Collab Todo Desktop 설치 가이드

## 시스템 요구사항

- **운영체제**: Windows 10 이상 (64비트 권장)
- **메모리**: 최소 512MB RAM
- **디스크 공간**: 최소 100MB
- **네트워크**: 서버의 MySQL 데이터베이스에 대한 네트워크 연결

## 설치 방법

### 1. 설치 프로그램 실행

1. `CollabTodoDesktop-Setup-1.0.0.exe` 파일을 더블클릭하여 실행합니다.
2. 사용자 계정 컨트롤(UAC) 프롬프트가 나타나면 **예**를 클릭합니다.
3. 설치 마법사가 시작됩니다.

### 2. 설치 옵션 선택

- **설치 위치**: 
  - 기본값은 `C:\Program Files\Collab Todo Desktop`입니다.
  - **"찾아보기" 버튼을 클릭하여 원하는 설치 위치를 선택할 수 있습니다.**
  - 사용자 디렉토리나 다른 드라이브에도 설치 가능합니다.
  - 예: `D:\Programs\Collab Todo Desktop`, `C:\Users\사용자명\AppData\Local\Collab Todo Desktop`
- **바탕화면 바로가기**: 선택적으로 바탕화면에 바로가기를 생성할 수 있습니다.
- **빠른 실행 바로가기**: Windows 7 이하에서만 사용 가능합니다.

### 3. 설치 완료

설치가 완료되면 다음 옵션을 선택할 수 있습니다:
- **Collab Todo Desktop 실행**: 설치 후 즉시 프로그램을 실행합니다.

## 초기 설정

### 데이터베이스 연결 설정

프로그램을 처음 실행하기 전에 데이터베이스 연결 정보를 설정해야 합니다.

#### 방법 1: 환경 변수 설정 (권장)

1. **시스템 속성** 열기:
   - `Win + R` 키를 누릅니다
   - `sysdm.cpl`을 입력하고 Enter를 누릅니다
   - **고급** 탭 → **환경 변수** 클릭

2. **시스템 변수**에 다음 변수들을 추가합니다:

   ```
   COLLAB_TODO_DB_HOST=your-server-ip
   COLLAB_TODO_DB_PORT=3306
   COLLAB_TODO_DB_USER=your-username
   COLLAB_TODO_DB_PASSWORD=your-password
   COLLAB_TODO_DB_NAME=collab_todo
   COLLAB_TODO_DB_USE_SSL=0
   ```

3. **확인**을 클릭하여 저장합니다.

#### 방법 2: 설정 파일 사용 (향후 지원)

설정 파일을 통한 구성은 향후 버전에서 지원될 예정입니다.

### AI 서비스 설정 (선택사항)

AI 요약 기능을 사용하려면 다음 환경 변수를 추가합니다:

```
COLLAB_TODO_AI_BASE_URL=https://your-ai-service-url
COLLAB_TODO_AI_API_KEY=your-api-key
COLLAB_TODO_AI_TIMEOUT_SECONDS=15
```

## 프로그램 실행

### 시작 메뉴에서 실행

1. **시작** 메뉴를 클릭합니다
2. **Collab Todo Desktop**을 검색하거나 찾습니다
3. 프로그램을 클릭하여 실행합니다

### 바탕화면에서 실행

설치 시 바탕화면 바로가기를 생성했다면, 바탕화면의 **Collab Todo Desktop** 아이콘을 더블클릭합니다.

## 프로그램 제거

### 제어판을 통한 제거

1. **설정** → **앱** → **앱 및 기능**을 엽니다
2. **Collab Todo Desktop**을 찾습니다
3. **제거**를 클릭합니다
4. 제거 마법사의 지시를 따릅니다

### 시작 메뉴를 통한 제거

1. **시작** 메뉴에서 **Collab Todo Desktop** 폴더를 엽니다
2. **Collab Todo Desktop 제거**를 클릭합니다

## 문제 해결

### 프로그램이 시작되지 않습니다

1. **이벤트 뷰어**에서 오류 로그를 확인합니다:
   - `Win + X` → **이벤트 뷰어**
   - **Windows 로그** → **애플리케이션**에서 오류 확인

2. **바이러스 백신 소프트웨어**가 프로그램을 차단하는지 확인합니다.

3. **관리자 권한**으로 실행해 봅니다.

### 데이터베이스 연결 오류

1. **환경 변수**가 올바르게 설정되었는지 확인합니다.
2. **네트워크 연결**을 확인합니다 (서버에 접근 가능한지).
3. **방화벽 설정**을 확인합니다 (MySQL 포트 3306이 열려있는지).
4. **데이터베이스 서버**가 실행 중인지 확인합니다.

### "DB: 끊김" 상태가 계속 표시됩니다

1. 데이터베이스 연결 정보를 확인합니다.
2. 네트워크 연결을 테스트합니다:
   ```cmd
   ping your-server-ip
   ```
3. MySQL 포트가 열려있는지 확인합니다:
   ```cmd
   telnet your-server-ip 3306
   ```

## 추가 리소스

- **프로젝트 홈페이지**: [GitHub Repository](https://github.com/your-org/collab-todo-desktop)
- **문제 신고**: [Issues](https://github.com/your-org/collab-todo-desktop/issues)
- **문서**: 설치 디렉토리의 `docs` 폴더 참조

## 지원

문제가 발생하거나 질문이 있으시면:
- GitHub Issues를 통해 문의하세요
- 프로젝트 문서를 참조하세요

---

**버전**: 1.0.0  
**최종 업데이트**: 2025-01-XX

