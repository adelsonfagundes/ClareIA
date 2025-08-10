"""Gerador de emails de follow-up baseado em atas de reunião."""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.models.email import EmailFollowUp
from app.models.summary import MeetingSummary
from app.services.openai_client import get_openai_client

logger = logging.getLogger(__name__)


def generate_follow_up_email(
    summary: MeetingSummary,
    *,
    meeting_date: str | None = None,
    sender_name: str | None = None,
    company_name: str | None = None,
    custom_context: str | None = None,
) -> EmailFollowUp:
    """
    Gera email de follow-up baseado na ata da reunião.

    Args:
        summary: Ata da reunião gerada
        meeting_date: Data da reunião (opcional)
        sender_name: Nome de quem está enviando (opcional)
        company_name: Nome da empresa (opcional)
        custom_context: Contexto adicional (opcional)

    Returns:
        EmailFollowUp estruturado
    """
    settings = get_settings()
    client = get_openai_client()

    # Preparar contexto para o prompt
    context_parts = []
    if meeting_date:
        context_parts.append(f"Data da reunião: {meeting_date}")
    if sender_name:
        context_parts.append(f"Remetente: {sender_name}")
    if company_name:
        context_parts.append(f"Empresa: {company_name}")
    if custom_context:
        context_parts.append(f"Contexto adicional: {custom_context}")

    context_text = "\n".join(context_parts) if context_parts else ""

    # Prompt para gerar email estruturado
    system_prompt = """Você é um assistente especializado em comunicação corporativa.
    Sua tarefa é gerar um email de follow-up profissional e bem estruturado baseado na ata de uma reunião.

    Retorne um JSON válido com a seguinte estrutura:
    {
        "subject": "Assunto do email (máx 60 caracteres)",
        "greeting": "Saudação personalizada e calorosa",
        "summary": "Resumo executivo conciso (2-3 frases)",
        "key_decisions": ["Lista das principais decisões tomadas"],
        "action_items": ["Lista dos itens de ação formatados com responsável e prazo quando disponível"],
        "next_steps": "Próximos passos sugeridos (1-2 frases)",
        "closing": "Fechamento profissional e cordial"
    }

    DIRETRIZES:
    - Tom profissional mas acessível
    - Seja conciso e objetivo
    - Use linguagem clara e direta
    - Destaque informações importantes
    - Mantenha foco em ações e resultados
    - Use português brasileiro
    """

    user_prompt = f"""
Ata da reunião para gerar follow-up:

TÍTULO: {summary.title or "Reunião"}

RESUMO: {summary.summary}

PONTOS PRINCIPAIS:
{chr(10).join("- " + point for point in summary.key_points)}

DECISÕES TOMADAS:
{chr(10).join("- " + decision for decision in summary.decisions)}

ITENS DE AÇÃO:
{chr(10).join(f"- {item.description}" + (f" ({item.owner})" if item.owner else "") + (f" - até {item.due_date}" if item.due_date else "") for item in summary.action_items)}

INSIGHTS:
{chr(10).join("- " + insight for insight in summary.insights)}

{f"CONTEXTO ADICIONAL:{chr(10)}{context_text}" if context_text else ""}

Gere um email de follow-up profissional e estruturado.
"""

    logger.info("Gerando email de follow-up")

    try:
        response = client.chat.completions.create(
            model=settings.summary_model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.3,  # Mais conservador para emails profissionais
            response_format={"type": "json_object"},
            max_tokens=2000,
        )

        content = response.choices[0].message.content

        try:
            import json

            email_data = json.loads(content)
        except json.JSONDecodeError:
            logger.exception("Erro ao fazer parse do JSON do email")
            # Fallback com dados da ata
            email_data = _create_fallback_email(summary, meeting_date, sender_name)

        # Validar e criar email
        email = EmailFollowUp(
            subject=email_data.get("subject", f"Follow-up: {summary.title or 'Reunião'}"),
            greeting=email_data.get("greeting", "Olá pessoal,"),
            summary=email_data.get("summary", summary.summary),
            key_decisions=email_data.get("key_decisions", summary.decisions),
            action_items=email_data.get(
                "action_items",
                [
                    f"{item.description}"
                    + (f" ({item.owner})" if item.owner else "")
                    + (f" - até {item.due_date}" if item.due_date else "")
                    for item in summary.action_items
                ],
            ),
            next_steps=email_data.get("next_steps", "Aguardo confirmação dos próximos passos."),
            closing=email_data.get("closing", "Atenciosamente,"),
            meeting_date=meeting_date,
        )

        logger.info("Email de follow-up gerado com sucesso")
        return email

    except Exception:
        logger.exception("Erro ao gerar email de follow-up")
        # Fallback completo
        return _create_fallback_email(summary, meeting_date, sender_name)


def _create_fallback_email(
    summary: MeetingSummary, meeting_date: str | None = None, sender_name: str | None = None
) -> EmailFollowUp:
    """Cria email básico como fallback."""
    return EmailFollowUp(
        subject=f"Follow-up: {summary.title or 'Reunião'}",
        greeting="Olá pessoal,",
        summary=summary.summary,
        key_decisions=summary.decisions,
        action_items=[
            f"{item.description}"
            + (f" ({item.owner})" if item.owner else "")
            + (f" - até {item.due_date}" if item.due_date else "")
            for item in summary.action_items
        ],
        next_steps="Aguardo retorno sobre os próximos passos discutidos.",
        closing=f"Atenciosamente,{chr(10)}{sender_name or 'Equipe'}",
        meeting_date=meeting_date,
    )
