from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field

# Carrega automaticamente .env e .env.local
# - .env é carregado sem sobrescrever variáveis já definidas no ambiente
# - .env.local (se existir) pode sobrescrever valores do .env
try:
    from dotenv import load_dotenv, find_dotenv
except Exception:
    load_dotenv = None
    find_dotenv = None


def _load_env_files() -> None:
    """
    Carrega arquivos .env do diretório atual (ou pais) caso existam.

    Prioridade:
    1) Variáveis já existentes no ambiente (nunca são sobrescritas por arquivos)
    2) .env (override=False)
    3) .env.local (override=True) — útil para overrides locais por dev
    """
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
    """
    Configurações da aplicação, carregadas via variáveis de ambiente ou .env.
    Não depende de pydantic-settings; usamos python-dotenv para auto-load.
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
    )  # type: ignore[assignment]

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
