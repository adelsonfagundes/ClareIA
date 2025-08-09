from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """
    Configurações da aplicação, carregadas via variáveis de ambiente.
    Não depende de pydantic-settings para manter o stack enxuto.
    """

    # OpenAI
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_timeout: float = Field(
        default_factory=lambda: float(os.getenv("OPENAI_TIMEOUT", "120"))
    )
    openai_max_retries: int = Field(
        default_factory=lambda: int(os.getenv("OPENAI_MAX_RETRIES", "3"))
    )

    # Transcrição
    default_transcribe_model: str = os.getenv("TRANSCRIBE_MODEL", "gpt-4o-transcribe")
    default_language: str = os.getenv("TRANSCRIBE_LANGUAGE", "pt")
    default_response_format: Literal["text", "json", "verbose_json", "srt", "vtt"] = (
        os.getenv("TRANSCRIBE_FORMAT", "json")
    )

    # Summarizer
    summary_model: str = os.getenv("SUMMARY_MODEL", "gpt-4o-mini")
    summary_temperature: float = Field(
        default_factory=lambda: float(os.getenv("SUMMARY_TEMPERATURE", "0.2"))
    )


_settings_singleton: Settings | None = None


def get_settings() -> Settings:
    global _settings_singleton
    if _settings_singleton is None:
        _settings_singleton = Settings()
    return _settings_singleton
