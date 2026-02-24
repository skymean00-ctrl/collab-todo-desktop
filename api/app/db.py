from contextlib import contextmanager
import mysql.connector
from .config import get_settings


@contextmanager
def get_db():
    s = get_settings()
    conn = mysql.connector.connect(
        host=s.db_host,
        port=s.db_port,
        user=s.db_user,
        password=s.db_password,
        database=s.db_name,
        autocommit=False,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
