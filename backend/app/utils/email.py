from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import get_settings

# FastMail 인스턴스를 지연 생성 (모듈 로드 시 .env 없어도 오류 없도록)
_fm = None

def _get_fm() -> FastMail:
    global _fm
    if _fm is None:
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
        _fm = FastMail(mail_config)
    return _fm


async def send_notification_email(to: str, subject: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[to],
        body=body,
        subtype=MessageType.html,
    )
    await _get_fm().send_message(message)


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


async def send_verification_email(to: str, name: str, verify_url: str):
    subject = "[CollabTodo] 이메일 인증을 완료해주세요"
    body = f"""
    <div style="font-family: 'Malgun Gothic', sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
      <h2 style="color: #4f46e5;">CollabTodo 이메일 인증</h2>
      <p>안녕하세요, <b>{name}</b>님. 회원가입을 진심으로 환영합니다!</p>
      <p>아래 버튼을 클릭하여 이메일 인증을 완료해주세요.<br>
         인증 링크는 <b>24시간</b> 동안 유효합니다.</p>
      <div style="text-align: center; margin: 32px 0;">
        <a href="{verify_url}"
           style="background-color: #4f46e5; color: white; padding: 14px 32px;
                  border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">
          이메일 인증하기
        </a>
      </div>
      <p style="color: #6b7280; font-size: 13px;">
        버튼이 작동하지 않으면 아래 링크를 브라우저에 복사하여 접속하세요.<br>
        <a href="{verify_url}" style="color: #4f46e5;">{verify_url}</a>
      </p>
      <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
      <p style="color: #9ca3af; font-size: 12px;">본인이 가입하지 않으셨다면 이 메일을 무시하셔도 됩니다.</p>
    </div>
    """
    await send_notification_email(to, subject, body)
