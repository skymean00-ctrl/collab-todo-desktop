# Ubuntu 서버 배포 가이드

## 구성

```
폰/브라우저 → https://todo.skymeanai.com → Cloudflare Tunnel → nginx(80)
                                                                   ├── /       → React 정적 파일
                                                                   └── /api/   → FastAPI(8000)
PC Electron 앱 → https://todo.skymeanai.com/api/ → 동일 경로
```

---

## 1. 필수 패키지 설치

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx mysql-server
```

---

## 2. MySQL 설정

```bash
sudo mysql_secure_installation
sudo mysql -u root -p
```

```sql
CREATE DATABASE collab_todo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'collab_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON collab_todo.* TO 'collab_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# 스키마 적용
mysql -u collab_user -p collab_todo < /home/user/collab-todo-desktop/sql/schema.sql
```

---

## 3. FastAPI 백엔드 설정

```bash
cd /home/user/collab-todo-desktop/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env 설정
cp .env.example .env
nano .env
# APP_BASE_URL=https://todo.skymeanai.com 확인
```

### systemd 서비스 등록

```bash
sudo nano /etc/systemd/system/collabtodo-api.service
```

```ini
[Unit]
Description=CollabTodo FastAPI Backend
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/user/collab-todo-desktop/backend
ExecStart=/home/user/collab-todo-desktop/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=/home/user/collab-todo-desktop/backend/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable collabtodo-api
sudo systemctl start collabtodo-api
```

---

## 4. React 프론트엔드 빌드 및 배포

로컬 PC(개발 환경)에서:

```bash
cd frontend
npm install
npm run build
```

빌드된 `frontend/dist/` 폴더를 서버로 복사:

```bash
# 서버에서 디렉토리 생성
sudo mkdir -p /var/www/collabtodo
sudo chown -R $USER:$USER /var/www/collabtodo

# 로컬에서 업로드 (scp 또는 Tailscale SSH)
scp -r frontend/dist/* user@서버IP:/var/www/collabtodo/
```

---

## 5. nginx 설정

```bash
sudo cp /home/user/collab-todo-desktop/nginx.conf /etc/nginx/sites-available/collabtodo
sudo ln -s /etc/nginx/sites-available/collabtodo /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # 기본 설정 비활성화
sudo nginx -t   # 설정 검증
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 6. Cloudflare Tunnel 설정

```bash
# cloudflared 설치
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared jammy main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared -y

# 로그인 (브라우저에서 skymeanai.com 승인)
cloudflared tunnel login

# 터널 생성
cloudflared tunnel create collabtodo
```

`~/.cloudflared/config.yml` 작성:

```yaml
tunnel: <생성된-UUID>
credentials-file: /root/.cloudflared/<생성된-UUID>.json

ingress:
  - hostname: todo.skymeanai.com
    service: http://localhost:80    # nginx로 연결 (React + API 모두 처리)
  - service: http_status:404
```

```bash
# DNS 등록
cloudflared tunnel route dns collabtodo todo.skymeanai.com

# 서비스 등록
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

---

## 7. 동작 확인

```bash
# 브라우저에서 확인
https://todo.skymeanai.com          # React 앱 로딩
https://todo.skymeanai.com/api/health  # {"status": "ok"}

# 로그 확인
sudo journalctl -u collabtodo-api -f
sudo journalctl -u cloudflared -f
sudo journalctl -u nginx -f
```

---

## 8. 이후 프론트엔드 업데이트 방법

```bash
# 로컬에서 빌드 후 서버 업로드
npm run build
scp -r frontend/dist/* user@서버IP:/var/www/collabtodo/
```

---

## PC 앱 SetupPage 입력값

각 PC 최초 실행 시:
```
https://todo.skymeanai.com
```
