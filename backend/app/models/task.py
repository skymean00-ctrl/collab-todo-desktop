from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    Date, ForeignKey, Enum, DECIMAL, BigInteger, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class PriorityEnum(str, enum.Enum):
    urgent = "urgent"
    high = "high"
    normal = "normal"
    low = "low"


class StatusEnum(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    review = "review"
    approved = "approved"
    rejected = "rejected"


# 업무-태그 연결 테이블
task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), default="#6366f1")

    tasks = relationship("Task", back_populates="category")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)

    tasks = relationship("Task", secondary=task_tags, back_populates="tags")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    assigner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.normal)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    progress = Column(Integer, default=0)
    estimated_hours = Column(DECIMAL(5, 2))
    due_date = Column(Date)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"))
    is_subtask = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    assigner = relationship("User", foreign_keys=[assigner_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    category = relationship("Category", back_populates="tasks")
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")
    subtasks = relationship("Task", foreign_keys=[parent_task_id], backref="parent_task")
    attachments = relationship("Attachment", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="task")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    uploaded_at = Column(DateTime, server_default=func.now())

    task = relationship("Task", back_populates="attachments")
    uploader = relationship("User")


class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    old_value = Column(String(255))
    new_value = Column(String(255))
    comment = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    task = relationship("Task", back_populates="logs")
    user = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="SET NULL"))
    type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="notifications")
    task = relationship("Task", back_populates="notifications")
