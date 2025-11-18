# Linux에서 .NET SDK 설치 가이드

## 빠른 설치 (Ubuntu/Debian)

### 방법 1: 공식 설치 스크립트 (권장)

```bash
# .NET 8.0 SDK 설치
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --channel 8.0

# PATH에 추가 (현재 세션)
export PATH=$PATH:$HOME/.dotnet

# 영구적으로 PATH에 추가
echo 'export PATH=$PATH:$HOME/.dotnet' >> ~/.bashrc
source ~/.bashrc

# 설치 확인
dotnet --version
```

### 방법 2: 패키지 매니저 (Ubuntu 22.04+)

```bash
# Microsoft 패키지 저장소 추가
wget https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb

# .NET SDK 설치
sudo apt-get update
sudo apt-get install -y dotnet-sdk-8.0

# 설치 확인
dotnet --version
```

### 방법 3: Snap (간단하지만 최신 버전이 아닐 수 있음)

```bash
sudo snap install dotnet-sdk --classic --channel=8.0
```

## 설치 후 빌드

```bash
cd CollabTodoDesktop
./build_linux.sh
```

## 문제 해결

### dotnet 명령을 찾을 수 없음

PATH에 .dotnet 디렉토리가 추가되지 않았을 수 있습니다:

```bash
export PATH=$PATH:$HOME/.dotnet
dotnet --version
```

영구적으로 추가하려면:

```bash
echo 'export PATH=$PATH:$HOME/.dotnet' >> ~/.bashrc
source ~/.bashrc
```

### 권한 오류

일부 시스템에서는 sudo 권한이 필요할 수 있습니다:

```bash
sudo ./dotnet-install.sh --channel 8.0 --install-dir /usr/share/dotnet
```

---

**참고**: Linux에서 빌드한 Windows .exe 파일은 Windows PC에서만 실행할 수 있습니다.

