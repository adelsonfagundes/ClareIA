from __future__ import annotations

import json
import logging
import mimetypes
import os
from typing import Literal, Optional

from app.core.config import get_settings
from app.models.transcript import Transcript
from app.services.openai_client import get_openai_client

logger = logging.getLogger(__name__)

SupportedResponseFormat = Literal["text", "json", "verbose_json", "srt", "vtt"]


def _detect_mime(file_path: str) -> str:
    mime, _ = mimetypes.guess_type(file_path)
    return mime or "application/octet-stream"


def _ensure_audio(file_path: str) -> None:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    mime = _detect_mime(file_path)
    if not (mime.endswith("/mpeg") or mime.endswith("/wav") or mime == "audio/x-wav"):
        # Aceitamos mp3 (audio/mpeg) e wav (audio/wav, audio/x-wav)
        # Alguns sistemas podem não detectar corretamente; validamos também por extensão
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in {".mp3", ".wav"}:
            raise ValueError(f"Formato de arquivo não suportado: {mime} ({file_path})")


def transcribe_file(
    file_path: str,
    *,
    model: Optional[str] = None,
    language: Optional[str] = None,
    response_format: SupportedResponseFormat | None = None,
    prompt: Optional[str] = None,
) -> Transcript:
    """
    Transcreve arquivo de áudio usando OpenAI.

    Args:
        file_path: caminho do .mp3 ou .wav
        model: modelo de transcrição (gpt-4o-transcribe ou whisper-1)
        language: ISO 639-1 (ex: 'pt')
        response_format: 'text' | 'json' | 'verbose_json' | 'srt' | 'vtt'
        prompt: dica contextual para melhorar a precisão (opcional)

    Returns:
        Transcript
    """
    settings = get_settings()
    _ensure_audio(file_path)

    model = model or settings.default_transcribe_model
    language = language or settings.default_language
    response_format = response_format or settings.default_response_format

    client = get_openai_client()

    logger.info(f"Iniciando transcrição | arquivo={file_path} | modelo={model} | formato={response_format}")

    # Abre o arquivo como binário
    with open(file_path, "rb") as f:
        # Parâmetros aceitos variam por modelo; whisper-1 suporta verbose_json/srt/vtt
        params = {
            "model": model,
            "file": f,
            "language": language,
        }
        # Se for passado um prompt, ajuda em nomes próprios/termos técnicos
        if prompt:
            params["prompt"] = prompt

        # O SDK 1.x aceita response_format para controlar a saída
        if response_format:
            params["response_format"] = response_format

        try:
            result = client.audio.transcriptions.create(**params)
        except Exception as e:
            logger.error(f"Erro na API de transcrição: {e}")
            raise

    # Algumas formas de extrair dados dependendo do formato
    # Tentamos acessar de forma resiliente para diferentes versões do SDK
    def to_dict(obj) -> dict:
        for attr in ("to_dict", "model_dump", "dict"):
            fn = getattr(obj, attr, None)
            if callable(fn):
                try:
                    d = fn()
                    if isinstance(d, dict):
                        return d
                except Exception:
                    pass
        # fallback: tentar obter JSON
        for attr in ("model_dump_json",):
            fn = getattr(obj, attr, None)
            if callable(fn):
                try:
                    return json.loads(fn())
                except Exception:
                    pass
        # último caso: não conseguimos converter
        return {}

    # Quando response_format == "verbose_json", result contém segments
    if response_format == "verbose_json":
        data = to_dict(result)
        transcript = Transcript.from_verbose_json(data, fallback_language=language, source_path=file_path)
    elif response_format in ("srt", "vtt"):
        # SRT/VTT são strings formatadas; guardamos também o texto limpo
        text_value = getattr(result, "text", None)
        if not isinstance(text_value, str):
            # Tentar extrair do dict
            data = to_dict(result)
            text_value = data.get("text") or ""
        transcript = Transcript(text=text_value, language=language, segments=None, source_path=file_path)
    else:
        # 'text' e 'json' normalmente retornam 'text'
        text_value = getattr(result, "text", None)
        if not isinstance(text_value, str):
            data = to_dict(result)
            text_value = data.get("text") or ""
        transcript = Transcript(text=text_value, language=language, segments=None, source_path=file_path)

    logger.info("Transcrição concluída com sucesso")
    return transcript


def save_transcript(transcript: Transcript, output_path: str, as_format: Literal["json", "txt"] = "json") -> None:
    """
    Salva a transcrição em JSON (modelo Pydantic) ou texto simples.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    if as_format == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcript.model_dump_json(ensure_ascii=False, indent=2))
    elif as_format == "txt":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcript.text)
    else:
        raise ValueError(f"Formato de saída não suportado: {as_format}")
    logger.info(f"Transcrição salva em {output_path}")
