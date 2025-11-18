"""
간단한 DB 연결 테스트 스크립트.

GUI 없이 터미널에서 실행하여 DB 설정 및 연결 가능 여부를 확인한다.
"""

from __future__ import annotations

from collab_todo.config import load_db_config
from collab_todo.db import DatabaseConnectionError, db_connection


def main() -> int:
    config = load_db_config()
    if config is None:
        print("DB 설정이 완료되지 않았습니다.")
        print("필수 환경 변수: COLLAB_TODO_DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME")
        return 1

    try:
        with db_connection(config) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            cursor.close()
    except DatabaseConnectionError as exc:
        print(f"데이터베이스 연결 오류: {exc}")
        return 2
    except Exception as exc:  # 예상치 못한 예외 방어
        print(f"알 수 없는 오류 발생: {exc}")
        return 3

    if not row or row[0] != 1:
        print("DB 응답이 예상과 다릅니다.")
        return 4

    print("DB 연결 및 기본 쿼리 테스트 성공.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


