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
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()
    mime = _detect_mime(file_path)
    if ext in SUPPORTED_EXTS or mime in SUPPORTED_MIMES:
        return
    raise ValueError(f"Formato de arquivo não suportado: {mime or ext} ({file_path}). Use .mp3, .wav ou .m4a.")


def _is_gpt4o_transcribe(model: str) -> bool:
    m = (model or "").lower()
    return m.startswith("gpt-4o-transcribe")


def _is_whisper_model(model: str) -> bool:
    m = (model or "").lower()
    return m.startswith("whisper")


def _validate_model_and_format(model: str, response_format: SupportedResponseFormat) -> None:
    """
    gpt-4o-transcribe: suporta apenas 'json' e 'text'.
    whisper-1: suporta 'text', 'json', 'verbose_json', 'srt', 'vtt'.
    """
    if _is_gpt4o_transcribe(model):
        if response_format not in {"json", "text"}:
            raise ValueError(
                f"O modelo '{model}' não suporta '{response_format}'. "
                "Use '--format json' ou '--format text', ou troque para '-m whisper-1' "
                "se precisar de 'verbose_json'/'srt'/'vtt'."
            )
    elif _is_whisper_model(model):
        if response_format not in {"text", "json", "verbose_json", "srt", "vtt"}:
            raise ValueError(
                f"O formato '{response_format}' não é suportado por '{model}'. "
                "Use um dos: text, json, verbose_json, srt, vtt."
            )
    else:
        # Desconhecido: permitir apenas text/json para segurança
        if response_format not in {"json", "text"}:
            raise ValueError(
                f"O formato '{response_format}' pode não ser suportado por '{model}'. "
                "Use 'json' ou 'text', ou escolha '-m whisper-1' para formatos avançados."
            )


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
        file_path: caminho do .mp3, .wav ou .m4a
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

    # Valida compatibilidade antes de chamar a API
    _validate_model_and_format(model, response_format)

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
            json.dump(transcript.model_dump(), f, ensure_ascii=False, indent=2)
    elif as_format == "txt":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcript.text)
    else:
        raise ValueError(f"Formato de saída não suportado: {as_format}")
    logger.info(f"Transcrição salva em {output_path}")
