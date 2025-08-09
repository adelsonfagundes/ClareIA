from __future__ import annotations

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    description: str = Field(description="Tarefa a ser executada")
    owner: str | None = Field(default=None, description="Responsável (se identificado)")
    due_date: str | None = Field(default=None, description="Prazo sugerido (AAAA-MM-DD ou texto)")


class MeetingSummary(BaseModel):
    title: str | None = Field(default=None, description="Título da reunião")
    summary: str = Field(description="Resumo executivo em português")
    key_points: list[str] = Field(default_factory=list, description="Principais pontos discutidos")
    decisions: list[str] = Field(default_factory=list, description="Decisões tomadas")
    action_items: list[ActionItem] = Field(default_factory=list, description="Ações a serem tomadas")
    insights: list[str] = Field(default_factory=list, description="Insights relevantes/métricas/risco")

    @staticmethod
    def system_instructions() -> str:
        return (
            "Você é um assistente especialista em reuniões corporativas. Dado o transcript em português do Brasil, "
            "gere uma ata clara e objetiva. Seja fiel ao conteúdo; use português natural; destaque decisões e tarefas."
        )
