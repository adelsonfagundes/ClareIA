from __future__ import annotations

import json
import logging
import mimetypes
from pathlib import Path
from typing import Literal

from app.core.config import get_settings
from app.models.transcript import Transcript
from app.services.openai_client import get_openai_client

logger = logging.getLogger(__name__)

# Garantir mapeamentos comuns para reconhecimento do tipo
mimetypes.add_type("audio/mp4", ".m4a")
mimetypes.add_type("audio/mpeg", ".mp3")
mimetypes.add_type("audio/wav", ".wav")

SupportedResponseFormat = Literal["text", "json", "verbose_json", "srt", "vtt"]

SUPPORTED_EXTS = {".mp3", ".wav", ".m4a"}
SUPPORTED_MIMES = {
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/x-m4a",
    "video/mp4",  # alguns sistemas identificam m4a como video/mp4
}


def _detect_mime(file_path: str) -> str:
    mime, _ = mimetypes.guess_type(file_path)
    return mime or "application/octet-stream"


def _ensure_audio(file_path: str) -> None:
    path_obj = Path(file_path)
    if not path_obj.is_file():
        msg = f"Arquivo não encontrado: {file_path}"
        raise FileNotFoundError(msg)

    ext = path_obj.suffix.lower()
    mime = _detect_mime(file_path)

    if ext in SUPPORTED_EXTS or mime in SUPPORTED_MIMES:
        return

    msg = f"Formato de arquivo não suportado: {mime or ext} ({file_path}). Use .mp3, .wav ou .m4a."
    raise ValueError(msg)


def _is_gpt4o_transcribe(model: str) -> bool:
    m = (model or "").lower()
    return m.startswith("gpt-4o-transcribe")


def _is_whisper_model(model: str) -> bool:
    m = (model or "").lower()
    return m.startswith("whisper")


def _validate_model_and_format(model: str, response_format: SupportedResponseFormat) -> None:
    """Valida compatibilidade entre modelo e formato."""
    if _is_gpt4o_transcribe(model):
        if response_format not in {"json", "text"}:
            msg = (
                f"O modelo '{model}' não suporta '{response_format}'. "
                "Use '--format json' ou '--format text', ou troque para '-m whisper-1' "
                "se precisar de 'verbose_json'/'srt'/'vtt'."
            )
            raise ValueError(msg)
    elif _is_whisper_model(model):
        if response_format not in {"text", "json", "verbose_json", "srt", "vtt"}:
            msg = (
                f"O formato '{response_format}' não é suportado por '{model}'. "
                "Use um dos: text, json, verbose_json, srt, vtt."
            )
            raise ValueError(msg)
    elif response_format not in {"json", "text"}:
        msg = (
            f"O formato '{response_format}' pode não ser suportado por '{model}'. "
            "Use 'json' ou 'text', ou escolha '-m whisper-1' para formatos avançados."
        )
        raise ValueError(msg)


def _convert_result_to_dict(obj: object) -> dict:
    """Converte objeto da API para dicionário."""
    for attr in ("to_dict", "model_dump", "dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                d = fn()
                if isinstance(d, dict):
                    return d
            except Exception:
                logger.debug("Falha ao converter com %s", attr)

    for attr in ("model_dump_json",):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return json.loads(fn())
            except Exception:
                logger.debug("Falha ao converter JSON com %s", attr)
    return {}


def _process_transcription_result(
    result: object,
    response_format: str,
    language: str,
    file_path: str,
) -> Transcript:
    """Processa o resultado da transcrição e retorna um Transcript."""
    if response_format == "verbose_json":
        data = _convert_result_to_dict(result)
        return Transcript.from_verbose_json(data, fallback_language=language, source_path=file_path)

    if response_format in ("srt", "vtt"):
        text_value = getattr(result, "text", None)
        if not isinstance(text_value, str):
            data = _convert_result_to_dict(result)
            text_value = data.get("text") or ""
        return Transcript(text=text_value, language=language, segments=None, source_path=file_path)

    # Para 'text' e 'json'
    text_value = getattr(result, "text", None)
    if not isinstance(text_value, str):
        data = _convert_result_to_dict(result)
        text_value = data.get("text") or ""
    return Transcript(text=text_value, language=language, segments=None, source_path=file_path)


def transcribe_file(
    file_path: str,
    *,
    model: str | None = None,
    language: str | None = None,
    response_format: SupportedResponseFormat | None = None,
    prompt: str | None = None,
) -> Transcript:
    """Transcreve arquivo de áudio usando OpenAI."""
    settings = get_settings()
    _ensure_audio(file_path)

    model = model or settings.default_transcribe_model
    language = language or settings.default_language
    response_format = response_format or settings.default_response_format

    _validate_model_and_format(model, response_format)

    client = get_openai_client()

    logger.info("Iniciando transcrição | arquivo=%s | modelo=%s | formato=%s", file_path, model, response_format)

    path_obj = Path(file_path)
    with path_obj.open("rb") as f:
        params = {
            "model": model,
            "file": f,
            "language": language,
        }
        if prompt:
            params["prompt"] = prompt
        if response_format:
            params["response_format"] = response_format

        try:
            result = client.audio.transcriptions.create(**params)
        except Exception:
            logger.exception("Erro na API de transcrição")
            raise

    transcript = _process_transcription_result(result, response_format, language, file_path)

    logger.info("Transcrição concluída com sucesso")
    return transcript


def save_transcript(transcript: Transcript, output_path: str, as_format: Literal["json", "txt"] = "json") -> None:
    """Salva a transcrição em JSON (modelo Pydantic) ou texto simples."""
    path_obj = Path(output_path).resolve()
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    if as_format == "json":
        with path_obj.open("w", encoding="utf-8") as f:
            json.dump(transcript.model_dump(), f, ensure_ascii=False, indent=2)
    elif as_format == "txt":
        with path_obj.open("w", encoding="utf-8") as f:
            f.write(transcript.text)
    else:
        msg = f"Formato de saída não suportado: {as_format}"
        raise ValueError(msg)

    logger.info("Transcrição salva em %s", output_path)
