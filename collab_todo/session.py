"""
세션 관리.

로그인 후 현재 사용자 정보를 앱 전체에서 참조할 수 있도록 한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from collab_todo.models import User


@dataclass
class Session:
    """현재 로그인된 사용자 세션."""

    user: Optional[User] = None

    @property
    def is_logged_in(self) -> bool:
        return self.user is not None

    @property
    def user_id(self) -> int:
        if self.user is None:
            raise RuntimeError("로그인되지 않은 상태입니다.")
        return self.user.id

    @property
    def display_name(self) -> str:
        if self.user is None:
            return ""
        return self.user.display_name

    @property
    def is_admin(self) -> bool:
        if self.user is None:
            return False
        return self.user.role == "admin"

    def login(self, user: User) -> None:
        self.user = user

    def logout(self) -> None:
        self.user = None
