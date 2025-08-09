from __future__ import annotations

import json
import logging
from typing import Optional

from app.core.config import get_settings
from app.models.summary import MeetingSummary
from app.models.transcript import Transcript
from app.services.openai_client import get_openai_client

logger = logging.getLogger(__name__)


def summarize_transcript(
    transcript: Transcript | str,
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    extra_context: Optional[str] = None,
) -> MeetingSummary:
    """
    Gera ata/insights estruturados a partir do transcript usando o Responses API.
    Retorna um MeetingSummary validado pelo Pydantic.
    """
    settings = get_settings()
    client = get_openai_client()

    model = model or settings.summary_model
    temperature = settings.summary_temperature if temperature is None else temperature

    text = transcript.text if isinstance(transcript, Transcript) else str(transcript)

    system_prompt = MeetingSummary.system_instructions()
    user_prompt = (
        "Transcrição em português do Brasil abaixo. Extraia uma ata clara, decisões, itens de ação e insights.\n\n"
        f"{('Contexto adicional:\n' + extra_context + '\n\n') if extra_context else ''}"
        "Transcript:\n"
        f"{text}"
    )

    # Construímos o schema diretamente do Pydantic para obter JSON validado
    schema = MeetingSummary.model_json_schema()

    logger.info(f"Gerando ata/insights | modelo={model}")

    try:
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
            ],
            temperature=temperature,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "MeetingSummary",
                    "schema": schema,
                    "strict": True,
                },
            },
        )
    except Exception as e:
        logger.error(f"Erro na API de resumo: {e}")
        raise

    # Quando usamos json_schema strict, o SDK expõe 'output_parsed'
    parsed = getattr(resp, "output_parsed", None)
    if parsed is None:
        # fallback: tenta extrair texto e fazer json.loads
        try:
            # resp.output_text pode existir nas versões recentes
            text_out = getattr(resp, "output_text", None)
            if not text_out:
                # fallback para estrutura de content
                resp_dict = getattr(resp, "to_dict", None)
                if callable(resp_dict):
                    rd = resp_dict()
                else:
                    rd = json.loads(resp.model_dump_json())  # type: ignore
                # Tenta achar algum texto
                text_out = ""
                for item in rd.get("output", []):
                    for c in item.get("content", []):
                        if c.get("type") in ("output_text", "text") and isinstance(c.get("text"), str):
                            text_out += c["text"]
                if not text_out:
                    raise ValueError("Não foi possível extrair texto de saída do modelo.")
            parsed = json.loads(text_out)
        except Exception as e:
            logger.error(f"Falha ao interpretar JSON do resumo: {e}")
            raise

    try:
        summary = MeetingSummary.model_validate(parsed)
    except Exception as e:
        logger.error(f"Falha ao validar MeetingSummary: {e}")
        # Loga o JSON para depuração
        logger.debug(f"JSON recebido para validação: {json.dumps(parsed, ensure_ascii=False)[:2000]}")
        raise

    logger.info("Ata/insights gerados com sucesso")
    return summary
