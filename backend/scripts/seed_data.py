#!/usr/bin/env python3
"""
Collab Todo - 초기 시드 데이터 삽입 스크립트
============================================================
사용법:
  cd backend
  python scripts/seed_data.py

.env 파일이 backend/ 또는 부모 디렉토리에 있어야 합니다.
============================================================
"""
import sys
import os

# backend 디렉토리를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.user import Department, SystemSettings
from app.models.task import Category


def seed_departments(db):
    DEFAULT_DEPARTMENTS = [
        "현장소장", "공무팀", "공사팀", "안전팀", "품질팀", "직영팀",
    ]
    added = 0
    for name in DEFAULT_DEPARTMENTS:
        exists = db.query(Department).filter_by(name=name).first()
        if not exists:
            db.add(Department(name=name))
            added += 1
    return added


def seed_categories(db):
    DEFAULT_CATEGORIES = [
        ("기획",     "#6366f1"),
        ("개발",     "#3b82f6"),
        ("영업",     "#10b981"),
        ("디자인",   "#f59e0b"),
        ("총무/인사", "#ef4444"),
        ("기타",     "#6b7280"),
    ]
    added = 0
    for name, color in DEFAULT_CATEGORIES:
        exists = db.query(Category).filter_by(name=name).first()
        if not exists:
            db.add(Category(name=name, color=color))
            added += 1
    return added


def seed_system_settings(db):
    DEFAULTS = [
        ("access_token_expire_minutes", "60",
         "Access JWT 만료 시간 (분)"),
        ("refresh_token_expire_days", "7",
         "Refresh Token 만료 일수"),
        ("max_upload_size_mb", "10",
         "파일 업로드 최대 크기 (MB)"),
        ("allowed_file_types", "pdf,docx,xlsx,pptx,jpg,jpeg,png,gif,zip,hwp",
         "허용 파일 확장자 (쉼표 구분)"),
        ("max_refresh_tokens_per_user", "5",
         "사용자 당 최대 Refresh Token 수"),
        ("rate_limit_per_minute", "200",
         "분당 API 요청 제한"),
        ("due_soon_days_warning", "3",
         "마감 임박 경고 일수"),
        ("max_filter_presets", "10",
         "사용자 당 최대 필터 프리셋 수"),
        ("app_name", "CollabTodo",
         "서비스 이름"),
        ("app_version", "2.0.0",
         "현재 버전"),
    ]
    added = 0
    for key, value, description in DEFAULTS:
        exists = db.query(SystemSettings).filter_by(key=key).first()
        if not exists:
            db.add(SystemSettings(key=key, value=value, description=description))
            added += 1
    return added


def main():
    print("=" * 60)
    print("Collab Todo - 시드 데이터 삽입")
    print("=" * 60)

    db = SessionLocal()
    try:
        dept_count = seed_departments(db)
        cat_count = seed_categories(db)
        setting_count = seed_system_settings(db)
        db.commit()

        print(f"✓ 부서: {dept_count}개 추가")
        print(f"✓ 카테고리: {cat_count}개 추가")
        print(f"✓ 시스템 설정: {setting_count}개 추가")
        print("\n시드 데이터 삽입 완료!")
    except Exception as e:
        db.rollback()
        print(f"\n오류 발생: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
