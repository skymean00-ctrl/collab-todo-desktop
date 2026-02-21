from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.models import user, task  # noqa: F401 - 테이블 등록용
from app.routers import auth, users, tasks, attachments, notifications, categories, admin
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="CollabTodo API",
    version="1.0.0",
    lifespan=lifespan,
)

from app.config import get_settings as _get_settings
_settings = _get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.allowed_origins,  # .env의 ALLOWED_ORIGINS (기본값: 배포 도메인)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"status": "ok"}
