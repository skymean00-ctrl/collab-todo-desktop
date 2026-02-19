# Collab Todo Desktop - C# / .NET 버전

Windows용 협업 워크플로우 할 일 관리 프로그램 (C# / .NET 버전)

## 주요 특징

- ✅ **단일 실행 파일**: Python 설치 없이 바로 실행 가능
- ✅ **Self-contained 배포**: 모든 의존성 포함 (50-80MB)
- ✅ **간편한 배포**: 단일 .exe 파일만 배포하면 됨
- ✅ **Python 버전과 100% 기능 동일**
- ✅ **증분 동기화**: 변경된 데이터만 가져와서 효율적
- ✅ **실시간 대시보드**: 작업 상태 및 통계 실시간 표시

## 빠른 시작

### 1. 다운로드

`CollabTodoDesktop.exe` 파일을 다운로드합니다.

### 2. 설정

실행 파일과 같은 폴더에 `appsettings.json` 파일을 생성합니다:

```json
{
  "Database": {
    "Host": "192.168.1.100",
    "Port": 3306,
    "User": "your_username",
    "Password": "your_password",
    "Database": "collab_todo",
    "UseSsl": false
  }
}
```

### 3. 실행

`CollabTodoDesktop.exe` 더블 클릭하여 실행합니다.

## 시스템 요구사항

- Windows 10 이상 (64비트)
- 서버의 MySQL 데이터베이스에 네트워크 접근 가능
- **Python 설치 불필요**

## 상세 문서

- [설치 및 실행 가이드](docs/INSTALLATION_GUIDE_CSHARP.md)
- [빌드 가이드](BUILD_INSTALLER.md) (개발자용)

## Python 버전과의 차이점

| 항목 | Python 버전 | C# / .NET 버전 |
|------|------------|----------------|
| 런타임 | Python 3.11+ 필요 | 포함됨 (self-contained) |
| 배포 파일 크기 | 100-200MB | 50-80MB |
| 설치 과정 | Python + PyInstaller | 단일 .exe 파일 |
| 시작 속도 | 느림 (인터프리터) | 빠름 (네이티브) |
| 기능 | 동일 | 동일 |

## 개발자 정보

### 빌드 방법

```bash
cd CollabTodoDesktop
dotnet build
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
```

빌드된 실행 파일: `bin/Release/net8.0/win-x64/publish/CollabTodoDesktop.exe`

### 기술 스택

- **.NET 8.0**: 런타임 및 프레임워크
- **WPF**: Windows Presentation Foundation (UI)
- **MySqlConnector**: MySQL 데이터베이스 연결
- **Microsoft.Extensions.Configuration**: 설정 관리
- **Microsoft.Extensions.DependencyInjection**: 의존성 주입

### 프로젝트 구조

```
CollabTodoDesktop/
├── Models/              # 도메인 모델
├── Repositories/        # 데이터 접근 레이어
├── Services/            # 비즈니스 로직
├── ViewModels/          # MVVM ViewModels
├── Views/               # WPF UI
├── Configuration/       # 설정 관리
└── Utils/               # 유틸리티
```

## 라이선스

[기존 라이선스와 동일]

## 기여

이슈 및 풀 리퀘스트 환영합니다!

---

**버전**: 1.0.0 (C# / .NET)  
**Python 버전**: [기존 Python 버전과 병행 개발]

