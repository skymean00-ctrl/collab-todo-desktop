# CollabTodo Desktop

건설 현장 협업 업무 관리 시스템.
FastAPI 백엔드 + React 웹앱 + Electron 데스크탑 앱 구성.

---

## 기술 스택

| 레이어 | 기술 |
|---|---|
| Backend | Python 3.11 · FastAPI · SQLAlchemy 2 · MySQL |
| Frontend | React 18 · Vite · Tailwind CSS · Zustand |
| Desktop | Electron (Windows `.exe` 인스톨러) |
| 배포 | Ubuntu + nginx + Cloudflare Tunnel |

---

## 디렉터리 구조

```
collab-todo-desktop/
├── backend/             # FastAPI 서버
│   ├── app/
│   │   ├── models/      # SQLAlchemy ORM 모델
│   │   ├── routers/     # API 엔드포인트
│   │   ├── utils/       # 인증·이메일 유틸
│   │   └── main.py
│   └── requirements.txt
├── frontend/            # React + Electron
│   ├── src/             # React 소스
│   ├── electron/        # Electron 메인 프로세스
│   └── package.json
├── sql/
│   └── schema.sql       # MySQL 스키마
├── nginx.conf           # nginx 설정 (서버 배포용)
├── SERVER_SETUP.md      # Ubuntu 서버 배포 가이드
└── .github/workflows/
    └── build-installer.yml  # Windows 인스톨러 빌드 CI
```

---

## 로컬 개발 환경 (빠른 시작)

### 사전 조건

- Python 3.11+
- Node.js 20+
- MySQL 8.0+

### 1. MySQL 스키마 적용

```bash
mysql -u root -p < sql/schema.sql
```

### 2. 백엔드 설정

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# .env 파일에서 DB_URL, SECRET_KEY 등 설정
```

`.env` 최소 설정:

```env
DATABASE_URL=mysql+pymysql://collab_user:your_password@localhost/collab_todo
SECRET_KEY=your-secret-key-32chars
APP_BASE_URL=http://localhost:5173
```

백엔드 실행:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. 프론트엔드 실행

```bash
cd frontend
npm install

# 웹 브라우저 개발 (Electron 없이)
npx vite

# Electron 데스크탑 앱 개발
npm run dev
```

브라우저에서 `http://localhost:5173` 접속.

---

## 빌드

### 웹 배포용 빌드 (Linux 서버 업로드)

```bash
cd frontend
npm run build:web      # → frontend/dist/ 생성
```

### Windows 인스톨러 빌드

```bash
cd frontend
npm run build          # vite 빌드 + electron-builder (Windows 환경에서 실행)
```

또는 GitHub에 `v*` 태그를 push하면 Actions에서 자동 빌드:

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 서버 배포

Ubuntu 서버 전체 배포 절차는 **[SERVER_SETUP.md](./SERVER_SETUP.md)** 참고.

---

## API 문서

백엔드 실행 후 자동 생성:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 주요 기능

- 업무 요청·배정·상태 관리 (대기 → 진행 → 검토 → 승인/반려)
- 자료요청 서브태스크
- 첨부파일 업로드/다운로드 (최대 50MB)
- 이메일 인증·알림
- 우선순위·날짜 범위 필터, 페이지네이션, CSV 내보내기
- 댓글, 업무 복사, 담당자 변경
- 관리자 사용자 관리 (활성화/비활성화)
- 다크모드

---

## 환경변수 목록

| 변수 | 설명 | 예시 |
|---|---|---|
| `DATABASE_URL` | MySQL 연결 URL | `mysql+pymysql://user:pass@localhost/collab_todo` |
| `SECRET_KEY` | JWT 서명 키 (32자 이상) | `openssl rand -hex 32` 출력값 |
| `APP_BASE_URL` | 이메일 인증 링크 기본 URL | `https://todo.skymeanai.com` |
| `SMTP_HOST` | 이메일 발송 서버 | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP 포트 | `587` |
| `SMTP_USER` | 발송 계정 | `noreply@example.com` |
| `SMTP_PASS` | 발송 계정 비밀번호 | — |
| `FILE_STORAGE_PATH` | 첨부파일 저장 경로 | `/home/user/uploads` |
