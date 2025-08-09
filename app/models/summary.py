from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    description: str = Field(description="Tarefa a ser executada")
    owner: Optional[str] = Field(default=None, description="Responsável (se identificado)")
    due_date: Optional[str] = Field(default=None, description="Prazo sugerido (AAAA-MM-DD ou texto)")


class MeetingSummary(BaseModel):
    title: Optional[str] = Field(default=None, description="Título da reunião")
    summary: str = Field(description="Resumo executivo em português")
    key_points: List[str] = Field(default_factory=list, description="Principais pontos discutidos")
    decisions: List[str] = Field(default_factory=list, description="Decisões tomadas")
    action_items: List[ActionItem] = Field(default_factory=list, description="Ações a serem tomadas")
    insights: List[str] = Field(default_factory=list, description="Insights relevantes/métricas/risco")

    @staticmethod
    def system_instructions() -> str:
        return (
            "Você é um assistente especialista em reuniões corporativas. Dado o transcript em português do Brasil, "
            "gere uma ata clara e objetiva. Seja fiel ao conteúdo; use português natural; destaque decisões e tarefas."
        )
