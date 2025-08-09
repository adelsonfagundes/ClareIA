from __future__ import annotations

import json
import logging
import re

from app.core.config import get_settings
from app.models.summary import MeetingSummary
from app.models.transcript import Transcript
from app.services.openai_client import get_openai_client

logger = logging.getLogger(__name__)

# Constante para limite de resumo
SUMMARY_PREVIEW_LENGTH = 500


def _extract_json_from_content(content: str) -> dict | None:
    """Extrai JSON de uma string de conteúdo."""
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return None
    return None


def _create_fallback_summary(text: str) -> MeetingSummary:
    """Cria um resumo básico como fallback."""
    preview = text[:SUMMARY_PREVIEW_LENGTH] + "..." if len(text) > SUMMARY_PREVIEW_LENGTH else text
    return MeetingSummary(
        title="Transcrição Processada",
        summary=preview,
        key_points=["Não foi possível extrair pontos principais automaticamente"],
        decisions=[],
        action_items=[],
        insights=["Revise a transcrição manualmente para extrair insights"],
    )


def summarize_transcript(
    transcript: Transcript | str,
    *,
    model: str | None = None,
    temperature: float | None = None,
    extra_context: str | None = None,
) -> MeetingSummary:
    """Gera ata/insights estruturados a partir do transcript usando a API de chat."""
    settings = get_settings()
    client = get_openai_client()

    model = model or settings.summary_model
    temperature = settings.summary_temperature if temperature is None else temperature

    text = transcript.text if isinstance(transcript, Transcript) else str(transcript)

    # Instruções do sistema
    system_prompt = """Você é um assistente especialista em reuniões corporativas.
    Dado o transcript em português do Brasil, gere uma ata clara e objetiva.

    Retorne um JSON válido com a seguinte estrutura:
    {
        "title": "Título da reunião (opcional)",
        "summary": "Resumo executivo em português",
        "key_points": ["Lista de pontos principais discutidos"],
        "decisions": ["Lista de decisões tomadas"],
        "action_items": [
            {
                "description": "Tarefa a ser executada",
                "owner": "Responsável (opcional)",
                "due_date": "Prazo (opcional, formato AAAA-MM-DD ou texto)"
            }
        ],
        "insights": ["Lista de insights relevantes, métricas ou riscos identificados"]
    }

    Seja fiel ao conteúdo, use português natural e destaque decisões e tarefas importantes.
    Retorne APENAS o JSON, sem explicações adicionais."""

    # Prompt do usuário
    user_prompt = (
        "Transcrição em português do Brasil abaixo. Extraia uma ata clara, decisões, itens de ação e insights.\n\n"
    )

    if extra_context:
        user_prompt += f"Contexto adicional:\n{extra_context}\n\n"

    user_prompt += f"Transcript:\n{text}"

    logger.info("Gerando ata/insights | modelo=%s", model)

    try:
        # Usa a API de chat completions padrão
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=4000,
        )

        content = response.choices[0].message.content

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            logger.exception("Falha ao fazer parse do JSON")
            logger.debug("Resposta recebida: %s", content[:500])

            parsed = _extract_json_from_content(content)
            if not parsed:
                msg = f"Não foi possível extrair JSON válido da resposta: {e}"
                raise ValueError(msg) from e

        summary = MeetingSummary.model_validate(parsed)

    except Exception as e:
        logger.exception("Erro na API de resumo")
        logger.info("Tentando fallback sem response_format...")

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=temperature,
                max_tokens=4000,
            )

            content = response.choices[0].message.content
            parsed = _extract_json_from_content(content)

            if parsed:
                summary = MeetingSummary.model_validate(parsed)
            else:
                logger.warning("Criando resumo básico como fallback")
                summary = _create_fallback_summary(text)

        except Exception as fallback_error:
            logger.exception("Fallback também falhou")
            msg = f"Não foi possível gerar o resumo: {e}"
            raise ValueError(msg) from fallback_error

    logger.info("Ata/insights gerados com sucesso")
    return summary
