# Collab Todo Desktop - C# / .NET 빌드 가이드

## 사전 요구사항

### 필수
- **.NET 8.0 SDK** 이상
  - 다운로드: https://dotnet.microsoft.com/download/dotnet/8.0
  - 설치 확인: `dotnet --version` (8.0.x 이상)
  - **Windows 또는 Linux에서 빌드 가능** (크로스 플랫폼 빌드 지원)

### 빌드 환경
- **Windows**: Windows 10 이상 (64비트)
- **Linux**: Ubuntu 20.04+, Debian 11+, 또는 기타 Linux 배포판

### 선택사항
- Visual Studio 2022 Community (무료)
  - 또는 Visual Studio Code
  - 또는 Rider

## 빠른 빌드

### Windows에서 빌드

1. **프로젝트 폴더로 이동**
   ```cmd
   cd CollabTodoDesktop
   ```

2. **빌드 스크립트 실행**
   ```cmd
   build_release.bat
   ```

3. **실행 파일 확인**
   - 위치: `bin\Release\net8.0\win-x64\publish\CollabTodoDesktop.exe`
   - 크기: 약 50-80MB

### Linux에서 빌드 (크로스 플랫폼)

1. **.NET SDK 설치** (아직 설치하지 않은 경우)
   ```bash
   # Ubuntu/Debian
   wget https://dot.net/v1/dotnet-install.sh
   chmod +x dotnet-install.sh
   ./dotnet-install.sh --channel 8.0
   
   # 또는 패키지 매니저 사용
   # Ubuntu 22.04+
   sudo apt-get update
   sudo apt-get install -y dotnet-sdk-8.0
   ```

2. **프로젝트 폴더로 이동**
   ```bash
   cd CollabTodoDesktop
   ```

3. **빌드 스크립트 실행**
   ```bash
   ./build_linux.sh
   ```

4. **실행 파일 확인**
   - 위치: `bin/Release/net8.0/win-x64/publish/CollabTodoDesktop.exe`
   - 크기: 약 50-80MB
   - **Windows PC로 전송하여 사용**

### 방법 2: 명령줄에서 직접 빌드

```cmd
cd CollabTodoDesktop

REM 빌드
dotnet build -c Release

REM 단일 실행 파일 생성
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true
```

## 빌드 옵션 설명

### Self-contained 배포

```cmd
--self-contained true
```
- .NET 런타임을 포함하여 배포
- 사용자가 .NET을 별도로 설치할 필요 없음
- 파일 크기: 50-80MB

### Single File 배포

```cmd
-p:PublishSingleFile=true
```
- 모든 의존성을 단일 .exe 파일로 패키징
- 실행 시 자동으로 압축 해제

### Native Libraries 포함

```cmd
-p:IncludeNativeLibrariesForSelfExtract=true
```
- 네이티브 라이브러리(MySqlConnector 등) 포함

### Ready-to-Run

```cmd
-p:PublishReadyToRun=true
```
- AOT 컴파일로 시작 속도 향상

## 빌드 결과

### 출력 위치

```
CollabTodoDesktop/
└── bin/
    └── Release/
        └── net8.0/
            └── win-x64/
                └── publish/
                    ├── CollabTodoDesktop.exe  ← 실행 파일
                    └── appsettings.json       ← 설정 파일 (있는 경우)
```

### 파일 크기

- **CollabTodoDesktop.exe**: 약 50-80MB
  - 모든 .NET 런타임 포함
  - 모든 NuGet 패키지 포함
  - 네이티브 라이브러리 포함

## 배포 준비

### 1. 실행 파일 복사

`CollabTodoDesktop.exe` 파일을 배포할 위치로 복사합니다.

### 2. 설정 파일 생성 (선택사항)

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

### 3. 배포

- 실행 파일과 설정 파일을 함께 배포
- 또는 실행 파일만 배포 (환경 변수 사용)

## 문제 해결

### .NET SDK가 설치되지 않음

**오류**: `'dotnet'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는 배치 파일이 아닙니다.`

**해결**:
1. .NET 8.0 SDK 다운로드: https://dotnet.microsoft.com/download/dotnet/8.0
2. 설치 후 명령 프롬프트 재시작
3. `dotnet --version`으로 확인

### 빌드 실패

**오류**: `error CS0006: Metadata file '...' could not be found`

**해결**:
1. NuGet 패키지 복원:
   ```cmd
   dotnet restore
   ```
2. 빌드 디렉토리 정리:
   ```cmd
   dotnet clean
   dotnet build
   ```

### 실행 파일이 너무 큼

**원인**: Self-contained 배포는 모든 런타임을 포함합니다.

**해결**:
- 파일 크기는 정상입니다 (50-80MB)
- Framework-dependent 배포로 변경하면 작아지지만, 사용자가 .NET을 설치해야 함

### 실행 파일이 실행되지 않음

**확인 사항**:
1. Windows 10 이상인지 확인
2. 바이러스 백신 소프트웨어 확인
3. 이벤트 뷰어에서 오류 확인

## 개발 빌드

### 디버그 빌드

```cmd
dotnet build -c Debug
```

### 개발 중 실행

```cmd
dotnet run
```

또는 Visual Studio에서 F5 키

## 고급 옵션

### 파일 크기 최적화

```cmd
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:PublishTrimmed=true
```

**주의**: `PublishTrimmed=true`는 일부 기능을 제거할 수 있습니다.

### 특정 플랫폼 타겟팅

```cmd
# Windows x64
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true

# Windows ARM64
dotnet publish -c Release -r win-arm64 --self-contained true -p:PublishSingleFile=true
```

## CI/CD 통합

### GitHub Actions 예제

```yaml
name: Build

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup .NET
      uses: actions/setup-dotnet@v3
      with:
        dotnet-version: '8.0.x'
    - name: Build
      run: dotnet build -c Release
    - name: Publish
      run: dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: CollabTodoDesktop
        path: CollabTodoDesktop/bin/Release/net8.0/win-x64/publish/CollabTodoDesktop.exe
```

## 참고 자료

- [.NET 배포 문서](https://docs.microsoft.com/dotnet/core/deploying/)
- [Single-file 배포](https://docs.microsoft.com/dotnet/core/deploying/single-file)
- [Self-contained 배포](https://docs.microsoft.com/dotnet/core/deploying/#publish-self-contained)

---

**버전**: 1.0.0  
**최종 업데이트**: 2025-01-XX

