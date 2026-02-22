# DB 관리 가이드

## 1. 초기 설치

### 새 설치 (전체 스키마 생성)
```bash
mysql -u root -p < sql/schema.sql
```

### 기존 DB 업그레이드 (v1 → v2)
```bash
mysql -u root -p collab_todo < sql/migrate_v2.sql
```

---

## 2. 마이그레이션 (Alembic)

Alembic을 사용하면 스키마 변경 이력을 코드로 관리하고 롤백도 가능합니다.

### 설치
```bash
cd backend
pip install alembic
```

### 현재 상태 확인
```bash
cd backend
alembic current
```

### v2 마이그레이션 적용
```bash
cd backend
alembic upgrade head
```

### 롤백 (1단계 이전으로)
```bash
cd backend
alembic downgrade -1
```

### 새 마이그레이션 파일 생성 (모델 변경 후)
```bash
cd backend
alembic revision --autogenerate -m "변경 내용 설명"
```

> **참고**: `alembic.ini`의 DB URL은 `.env` 파일에서 자동으로 읽힙니다.
> `alembic/env.py`가 `app.config.get_settings()`를 호출합니다.

---

## 3. 초기 데이터 삽입 (Seed)

부서, 카테고리, 시스템 설정 기본값을 삽입합니다.

```bash
cd backend
python scripts/seed_data.py
```

이미 존재하는 데이터는 건너뛰므로 중복 실행해도 안전합니다.

---

## 4. 백업

### 수동 백업
```bash
cd backend
./scripts/backup.sh
```

### 환경변수 커스터마이즈
```bash
DB_HOST=db.example.com DB_USER=app DB_PASSWORD=secret ./scripts/backup.sh
```

### 자동 백업 (cron)
```bash
# 매일 새벽 2시 백업, 30일치 보관
0 2 * * * /path/to/collab-todo-desktop/backend/scripts/backup.sh >> /var/log/collab_backup.log 2>&1
```

백업 파일은 `backups/` 디렉토리에 `.sql.gz` 형식으로 저장됩니다.

---

## 5. 모니터링

### 기본 헬스체크
```
GET /health
```
응답:
```json
{"status": "ok", "version": "2.0.0"}
```

### DB 헬스체크
```
GET /health/db
```
응답:
```json
{
  "status": "ok",
  "db_response_ms": 1.2,
  "tables_found": 15,
  "missing_tables": []
}
```

`status`가 `"degraded"`이면 일부 테이블이 누락된 것이므로 마이그레이션을 실행하세요.

---

## 6. 시스템 설정 (DB 기반)

하드코딩 대신 `system_settings` 테이블로 관리합니다.
관리자 페이지 → **설정 관리** 탭 또는 직접 SQL로 수정 가능합니다.

| key | 기본값 | 설명 |
|-----|--------|------|
| `access_token_expire_minutes` | `60` | Access JWT 만료 시간 (분) |
| `refresh_token_expire_days` | `7` | Refresh Token 만료 일수 |
| `max_upload_size_mb` | `10` | 파일 업로드 최대 크기 (MB) |
| `allowed_file_types` | `pdf,docx,...` | 허용 파일 확장자 |
| `max_refresh_tokens_per_user` | `5` | 사용자당 최대 Refresh Token 수 |
| `rate_limit_per_minute` | `200` | 분당 API 요청 제한 |
| `due_soon_days_warning` | `3` | 마감 임박 경고 일수 |
| `max_filter_presets` | `10` | 사용자당 최대 필터 프리셋 수 |

---

## 7. 권장 운영 체크리스트

- [ ] `.env` 파일에 `SECRET_KEY` 설정 (32자 이상 랜덤 문자열)
- [ ] 운영 서버에서 `allowed_origins`를 실제 도메인으로 제한
- [ ] 정기 백업 cron 등록
- [ ] `backups/` 디렉토리 접근 권한 제한 (`chmod 700`)
- [ ] MySQL 사용자에게 최소 권한만 부여 (SELECT, INSERT, UPDATE, DELETE)
- [ ] DB 연결 비밀번호 주기적 교체
- [ ] `/health/db` 엔드포인트를 외부 모니터링 도구(UptimeRobot 등)에 등록
