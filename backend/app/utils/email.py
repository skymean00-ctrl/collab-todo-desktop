from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import get_settings

settings = get_settings()

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

fm = FastMail(mail_config)


async def send_notification_email(to: str, subject: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[to],
        body=body,
        subtype=MessageType.html,
    )
    await fm.send_message(message)


async def send_task_assigned(to: str, assignee_name: str, task_title: str, assigner_name: str, due_date: str):
    subject = f"[CollabTodo] 새 업무가 배정되었습니다: {task_title}"
    body = f"""
    <p>안녕하세요, {assignee_name}님.</p>
    <p><b>{assigner_name}</b>님이 업무를 배정했습니다.</p>
    <p><b>업무:</b> {task_title}</p>
    <p><b>마감일:</b> {due_date}</p>
    <hr>
    <p>CollabTodo에 로그인하여 확인하세요.</p>
    """
    await send_notification_email(to, subject, body)


async def send_status_changed(to: str, user_name: str, task_title: str, old_status: str, new_status: str):
    status_map = {
        "pending": "대기",
        "in_progress": "진행중",
        "review": "검토요청",
        "approved": "승인(완료)",
        "rejected": "반려",
    }
    subject = f"[CollabTodo] 업무 상태 변경: {task_title}"
    body = f"""
    <p>안녕하세요, {user_name}님.</p>
    <p>업무 상태가 변경되었습니다.</p>
    <p><b>업무:</b> {task_title}</p>
    <p><b>변경:</b> {status_map.get(old_status, old_status)} → {status_map.get(new_status, new_status)}</p>
    <hr>
    <p>CollabTodo에 로그인하여 확인하세요.</p>
    """
    await send_notification_email(to, subject, body)


async def send_due_soon_reminder(to: str, user_name: str, task_title: str, due_date: str, days_left: int):
    subject = f"[CollabTodo] 마감 {days_left}일 전 알림: {task_title}"
    body = f"""
    <p>안녕하세요, {user_name}님.</p>
    <p>마감이 <b>{days_left}일</b> 남은 업무가 있습니다.</p>
    <p><b>업무:</b> {task_title}</p>
    <p><b>마감일:</b> {due_date}</p>
    <hr>
    <p>CollabTodo에 로그인하여 확인하세요.</p>
    """
    await send_notification_email(to, subject, body)
