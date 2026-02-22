from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())

    users = relationship("User", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    job_title = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    department = relationship("Department", back_populates="users")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    created_tasks = relationship("Task", foreign_keys="Task.assigner_id", back_populates="assigner")
    notifications = relationship("Notification", back_populates="user")
    verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    notification_preference = relationship(
        "UserNotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    filter_presets = relationship("FilterPreset", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("TaskFavorite", back_populates="user", cascade="all, delete-orphan")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="verification_tokens")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="reset_tokens")


class RefreshToken(Base):
    """Refresh Token — Access Token 만료 시 재발급용 (7일 유효)"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")


class UserNotificationPreference(Base):
    """사용자별 알림 수신 설정"""
    __tablename__ = "user_notification_preferences"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    # 앱 내 알림
    notify_assigned = Column(Boolean, default=True)
    notify_status_changed = Column(Boolean, default=True)
    notify_due_soon = Column(Boolean, default=True)
    notify_mentioned = Column(Boolean, default=True)
    notify_reassigned = Column(Boolean, default=True)
    notify_commented = Column(Boolean, default=True)
    # 이메일 알림
    email_assigned = Column(Boolean, default=True)
    email_status_changed = Column(Boolean, default=True)
    email_due_soon = Column(Boolean, default=True)
    email_mentioned = Column(Boolean, default=True)
    email_reassigned = Column(Boolean, default=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="notification_preference")


class FilterPreset(Base):
    """대시보드 필터 프리셋 — 자주 쓰는 필터 조합 저장"""
    __tablename__ = "filter_presets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    section = Column(String(50))
    status = Column(String(50))
    priority = Column(String(50))
    sort_by = Column(String(50))
    sort_dir = Column(String(10))
    due_date_from = Column(Date)
    due_date_to = Column(Date)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="filter_presets")


class SystemSettings(Base):
    """시스템 전역 설정 — 관리자가 DB에서 관리 (하드코딩 대체)"""
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TaskFavorite(Base):
    """업무 즐겨찾기"""
    __tablename__ = "task_favorites"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="favorites")
    task = relationship("Task", back_populates="favorites")
