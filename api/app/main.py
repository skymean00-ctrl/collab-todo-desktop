import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .routers import auth, sync, tasks, users, notifications, categories, attachments, bug_reports

app = FastAPI(
    title="Collab Todo API",
    description="collab-todo-desktop 백엔드 REST API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class NoCacheMiddleware(BaseHTTPMiddleware):
    """API 응답 캐시 방지"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response


app.add_middleware(NoCacheMiddleware)

app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(notifications.router)
app.include_router(categories.router)
app.include_router(attachments.router)
app.include_router(bug_reports.router)

# 앱 자동 업데이트 파일 서빙 (/updates/latest.yml, /updates/*.exe)
UPDATES_DIR = "/app/updates"
os.makedirs(UPDATES_DIR, exist_ok=True)
app.mount("/updates", StaticFiles(directory=UPDATES_DIR), name="updates")


@app.get("/health")
def health():
    return {"status": "ok"}
