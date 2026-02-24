#!/usr/bin/env python3
"""
collab-todo 사용자 생성 스크립트
사용법: python create_user.py
"""

import sys
import getpass
import mysql.connector
from passlib.context import CryptContext
from dotenv import load_dotenv
import os

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    return mysql.connector.connect(
        host=os.environ["COLLAB_TODO_DB_HOST"],
        port=int(os.getenv("COLLAB_TODO_DB_PORT", "3306")),
        user=os.environ["COLLAB_TODO_DB_USER"],
        password=os.environ["COLLAB_TODO_DB_PASSWORD"],
        database=os.getenv("COLLAB_TODO_DB_NAME", "collab_todo"),
    )


def create_user():
    print("=" * 40)
    print("  Collab To-Do 사용자 생성")
    print("=" * 40)

    username = input("아이디 (영문/숫자): ").strip()
    if not username:
        print("오류: 아이디를 입력하세요.")
        sys.exit(1)

    display_name = input("표시 이름 (예: 홍길동): ").strip()
    if not display_name:
        print("오류: 표시 이름을 입력하세요.")
        sys.exit(1)

    email = input("이메일: ").strip()

    role = input("권한 [user/admin] (기본: user): ").strip() or "user"
    if role not in ("user", "admin", "supervisor"):
        role = "user"

    password = getpass.getpass("비밀번호: ")
    password_confirm = getpass.getpass("비밀번호 확인: ")

    if password != password_confirm:
        print("오류: 비밀번호가 일치하지 않습니다.")
        sys.exit(1)

    if len(password) < 6:
        print("오류: 비밀번호는 6자 이상이어야 합니다.")
        sys.exit(1)

    password_hash = pwd_context.hash(password)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (username, display_name, email, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
            """,
            (username, display_name, email, password_hash, role),
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"\n✅ 사용자 생성 완료!")
        print(f"   ID: {user_id}")
        print(f"   아이디: {username}")
        print(f"   이름: {display_name}")
        print(f"   권한: {role}")
    except mysql.connector.IntegrityError as e:
        print(f"\n❌ 오류: 이미 존재하는 아이디 또는 이메일입니다. ({e})")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


def list_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, display_name, role, is_active FROM users ORDER BY id"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        print("등록된 사용자가 없습니다.")
        return

    print(f"\n{'ID':<5} {'아이디':<15} {'이름':<15} {'권한':<12} {'활성'}")
    print("-" * 55)
    for row in rows:
        active = "✅" if row[4] else "❌"
        print(f"{row[0]:<5} {row[1]:<15} {row[2]:<15} {row[3]:<12} {active}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "create"

    if cmd == "list":
        list_users()
    elif cmd == "create":
        create_user()
    else:
        print("사용법:")
        print("  python create_user.py          # 사용자 생성")
        print("  python create_user.py list     # 사용자 목록")
