from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Carrega automaticamente .env e .env.local
try:
    from dotenv import find_dotenv, load_dotenv
except Exception:
    load_dotenv = None
    find_dotenv = None


def _load_env_files() -> None:
    """Carrega arquivos .env do diretório atual (ou pais) caso existam."""
    if not load_dotenv or not find_dotenv:
        return

    # Carrega .env
    env_path = find_dotenv(filename=".env", usecwd=True)
    if env_path:
        load_dotenv(env_path, override=False)

    # Carrega .env.local depois, permitindo override do .env
    env_local_path = find_dotenv(filename=".env.local", usecwd=True)
    if env_local_path:
        load_dotenv(env_local_path, override=True)


# Executa no import do módulo (antes de consultar os valores)
_load_env_files()


class Settings(BaseModel):
    """Configurações da aplicação, carregadas via variáveis de ambiente ou .env."""

    # OpenAI
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_timeout: float = Field(default_factory=lambda: float(os.getenv("OPENAI_TIMEOUT", "120")))
    openai_max_retries: int = Field(default_factory=lambda: int(os.getenv("OPENAI_MAX_RETRIES", "3")))

    # Transcrição
    default_transcribe_model: str = os.getenv("TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
    default_language: str = os.getenv("TRANSCRIBE_LANGUAGE", "pt")
    default_response_format: Literal["text", "json", "verbose_json", "srt", "vtt"] = os.getenv(
        "TRANSCRIBE_FORMAT", "json"
    )  # type: ignore[assignment]

    # Summarizer
    summary_model: str = os.getenv("SUMMARY_MODEL", "gpt-4o-mini")
    summary_temperature: float = Field(default_factory=lambda: float(os.getenv("SUMMARY_TEMPERATURE", "0.2")))

    @field_validator("openai_timeout", mode="before")
    @classmethod
    def validate_timeout(cls, v):
        """Valida timeout como float."""
        try:
            return float(v)
        except (ValueError, TypeError):
            return 120.0

    @field_validator("openai_max_retries", mode="before")
    @classmethod
    def validate_max_retries(cls, v):
        """Valida max_retries como int."""
        try:
            return int(v)
        except (ValueError, TypeError):
            return 3

    @field_validator("summary_temperature", mode="before")
    @classmethod
    def validate_temperature(cls, v):
        """Valida temperature como float."""
        try:
            temp = float(v)
            # Garantir que está no range válido
            return max(0.0, min(1.0, temp))
        except (ValueError, TypeError):
            return 0.2


class SettingsManager:
    """Gerenciador de configurações singleton."""

    _instance: Settings | None = None

    @classmethod
    def get_instance(cls) -> Settings:
        """Retorna a instância singleton de Settings."""
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance


def get_settings() -> Settings:
    """Retorna as configurações da aplicação."""
    return SettingsManager.get_instance()
