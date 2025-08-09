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
    Gera ata/insights estruturados a partir do transcript usando a API de chat.
    Retorna um MeetingSummary validado pelo Pydantic.
    """
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

    logger.info(f"Gerando ata/insights | modelo={model}")

    try:
        # Usa a API de chat completions padrão
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=temperature,
            response_format={"type": "json_object"},  # Força resposta em JSON
            max_tokens=4000,
        )

        # Extrai o conteúdo da resposta
        content = response.choices[0].message.content

        # Parse do JSON
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Falha ao fazer parse do JSON: {e}")
            logger.debug(f"Resposta recebida: {content[:500]}")

            # Tenta extrair JSON de forma mais robusta
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except:
                    raise ValueError(f"Não foi possível extrair JSON válido da resposta: {e}")
            else:
                raise ValueError(f"Resposta não contém JSON válido: {e}")

        # Valida com Pydantic
        summary = MeetingSummary.model_validate(parsed)

    except Exception as e:
        logger.error(f"Erro na API de resumo: {e}")

        # Fallback: tenta sem response_format
        logger.info("Tentando fallback sem response_format...")

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=temperature,
                max_tokens=4000,
            )

            content = response.choices[0].message.content

            # Extrai JSON da resposta
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                summary = MeetingSummary.model_validate(parsed)
            else:
                # Último fallback: cria resumo básico
                logger.warning("Criando resumo básico como fallback")
                summary = MeetingSummary(
                    title="Transcrição Processada",
                    summary=text[:500] + "..." if len(text) > 500 else text,
                    key_points=["Não foi possível extrair pontos principais automaticamente"],
                    decisions=[],
                    action_items=[],
                    insights=["Revise a transcrição manualmente para extrair insights"],
                )
        except Exception as fallback_error:
            logger.error(f"Fallback também falhou: {fallback_error}")
            raise ValueError(f"Não foi possível gerar o resumo: {e}")

    logger.info("Ata/insights gerados com sucesso")
    return summary
