from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.database import engine, Base
from app.models import user, task  # noqa: F401 - 테이블 등록용
from app.routers import auth, users, tasks, attachments, notifications, categories, admin
from app.services.scheduler import start_scheduler, stop_scheduler
from app.config import get_settings

_settings = get_settings()

# Rate limiter 설정
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="CollabTodo API",
    version="2.0.0",
    lifespan=lifespan,
)

# Rate limiting 미들웨어
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 에러 핸들러 - 500 에러 표준화
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # FastAPI HTTPException은 그대로 통과
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."},
    )

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(attachments.router)
app.include_router(notifications.router)
app.include_router(categories.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/health/db")
def health_db():
    """DB 연결 상태 및 테이블 존재 확인 (모니터링용)"""
    from sqlalchemy import text
    from app.database import engine
    import time

    start = time.time()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

            # 핵심 테이블 존재 여부 확인
            tables_result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = DATABASE() ORDER BY table_name"
            ))
            tables = [row[0] for row in tables_result]

        elapsed_ms = round((time.time() - start) * 1000, 1)
        required = {
            "users", "tasks", "departments", "notifications",
            "refresh_tokens", "system_settings", "task_favorites",
            "user_notification_preferences", "filter_presets", "mentions",
        }
        missing = sorted(required - set(tables))

        return {
            "status": "ok" if not missing else "degraded",
            "db_response_ms": elapsed_ms,
            "tables_found": len(tables),
            "missing_tables": missing,
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": str(e)},
        )
