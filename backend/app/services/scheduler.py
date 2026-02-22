from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.database import SessionLocal
from app.models.task import Task, Notification, StatusEnum
from app.utils.email import send_due_soon_reminder

scheduler = AsyncIOScheduler()


async def check_due_soon():
    db: Session = SessionLocal()
    try:
        today = date.today()
        for days in [3, 1]:
            target_date = today + timedelta(days=days)
            tasks = db.query(Task).filter(
                Task.due_date == target_date,
                Task.status.notin_([StatusEnum.approved]),
            ).all()

            for task in tasks:
                assignee = task.assignee
                if not assignee:
                    continue

                # 중복 알림 방지
                already = db.query(Notification).filter(
                    Notification.user_id == assignee.id,
                    Notification.task_id == task.id,
                    Notification.type == f"due_soon_{days}d",
                ).first()
                if already:
                    continue

                db.add(Notification(
                    user_id=assignee.id,
                    task_id=task.id,
                    type=f"due_soon_{days}d",
                    message=f"마감 {days}일 전 알림: {task.title}",
                ))

                try:
                    await send_due_soon_reminder(
                        to=assignee.email,
                        user_name=assignee.name,
                        task_title=task.title,
                        due_date=str(task.due_date),
                        days_left=days,
                    )
                except Exception:
                    pass

        db.commit()
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(check_due_soon, "cron", hour=9, minute=0, timezone="Asia/Seoul")  # 매일 오전 9시 KST
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
