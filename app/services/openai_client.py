from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    settings = get_settings()
    # O SDK usa OPENAI_API_KEY do ambiente; passamos explicitamente para clareza
    return OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.openai_timeout,
        max_retries=settings.openai_max_retries,
    )
