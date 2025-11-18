"""
외부 LLM(요약 API) 호출용 클라이언트.

특정 벤더에 종속되지 않도록 HTTP 인터페이스만 정의한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests


@dataclass(frozen=True)
class AiSummaryConfig:
    base_url: str
    api_key: Optional[str]
    timeout_seconds: int = 15


class AiSummaryError(Exception):
    """AI 요약 호출 실패 시 사용하는 예외."""


def summarize_text(
    text: str,
    *,
    config: AiSummaryConfig,
    target_language: str = "ko",
) -> str:
    """
    주어진 텍스트를 요약 API에 전달하고 요약 결과를 문자열로 반환한다.

    - text가 비어 있으면 그대로 빈 문자열을 반환한다.
    - HTTP 오류, 타임아웃, 포맷 오류 등은 AiSummaryError로 감싼다.
    """
    cleaned = text.strip()
    if not cleaned:
        return ""

    headers = {
        "Content-Type": "application/json",
    }
    if config.api_key:
        # API 키는 헤더에만 포함하고, 다른 곳에 노출하지 않는다.
        headers["Authorization"] = f"Bearer {config.api_key}"

    payload = {
        "text": cleaned,
        "target_language": target_language,
    }

    try:
        response = requests.post(
            config.base_url.rstrip("/") + "/summarize",
            json=payload,
            headers=headers,
            timeout=config.timeout_seconds,
        )
    except requests.RequestException as exc:
        raise AiSummaryError(f"요약 서비스 요청 실패: {exc}") from exc

    if response.status_code != 200:
        raise AiSummaryError(f"요약 서비스 오류 상태 코드: {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise AiSummaryError("요약 서비스 응답을 JSON으로 파싱할 수 없습니다.") from exc

    summary = data.get("summary")
    if not isinstance(summary, str):
        raise AiSummaryError("요약 서비스 응답 형식이 올바르지 않습니다.")

    return summary.strip()


