#!/bin/bash
# Cloudflare Tunnel 설정 스크립트
# 실행: bash setup-tunnel.sh

CLOUDFLARED=~/.local/bin/cloudflared
TUNNEL_NAME="collab-todo-api"
DOMAIN="api.skymeanai.com"
LOCAL_PORT=8000

echo "======================================"
echo " Cloudflare Tunnel 설정"
echo " 도메인: $DOMAIN"
echo "======================================"
echo ""

# Step 1: 로그인
echo "[1/4] Cloudflare 로그인..."
echo "브라우저가 열리면 skymeanai.com 이 연결된 계정으로 로그인하세요."
$CLOUDFLARED tunnel login

# Step 2: 터널 생성
echo ""
echo "[2/4] 터널 생성 중..."
$CLOUDFLARED tunnel create $TUNNEL_NAME
TUNNEL_ID=$($CLOUDFLARED tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
echo "터널 ID: $TUNNEL_ID"

# Step 3: 설정 파일 생성
echo ""
echo "[3/4] 설정 파일 생성 중..."
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << EOF
tunnel: $TUNNEL_NAME
credentials-file: $HOME/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: $DOMAIN
    service: http://localhost:$LOCAL_PORT
  - service: http_status:404
EOF
echo "설정 파일: ~/.cloudflared/config.yml"

# Step 4: DNS 레코드 연결
echo ""
echo "[4/4] DNS 레코드 설정 중..."
$CLOUDFLARED tunnel route dns $TUNNEL_NAME $DOMAIN

echo ""
echo "======================================"
echo " 설정 완료!"
echo ""
echo " 터널 시작 명령어:"
echo " cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo " 또는 서비스로 등록:"
echo " sudo cloudflared service install"
echo "======================================"
