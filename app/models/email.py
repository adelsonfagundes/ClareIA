"""Modelos para geração de emails de follow-up."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EmailRecipient(BaseModel):
    """Destinatário do email."""

    name: str = Field(description="Nome do destinatário")
    email: str = Field(description="Endereço de email")
    role: str | None = Field(default=None, description="Papel na reunião (opcional)")


class EmailFollowUp(BaseModel):
    """Email de follow-up estruturado."""

    subject: str = Field(description="Assunto do email")
    greeting: str = Field(description="Saudação personalizada")
    summary: str = Field(description="Resumo executivo da reunião")
    key_decisions: list[str] = Field(default_factory=list, description="Principais decisões tomadas")
    action_items: list[str] = Field(default_factory=list, description="Itens de ação formatados")
    next_steps: str = Field(description="Próximos passos sugeridos")
    closing: str = Field(description="Fechamento do email")
    meeting_date: str | None = Field(default=None, description="Data da reunião")

    def to_html(self) -> str:
        """Converte o email para formato HTML."""
        decisions_html = ""
        if self.key_decisions:
            decisions_list = "\n".join(f"        <li>{decision}</li>" for decision in self.key_decisions)
            decisions_html = f"""
    <h3 style="color: #2c3e50; margin-top: 20px;">🎯 Principais Decisões</h3>
    <ul style="margin-left: 20px; line-height: 1.6;">
{decisions_list}
    </ul>"""

        actions_html = ""
        if self.action_items:
            actions_list = "\n".join(f"        <li>{action}</li>" for action in self.action_items)
            actions_html = f"""
    <h3 style="color: #e74c3c; margin-top: 20px;">📋 Itens de Ação</h3>
    <ul style="margin-left: 20px; line-height: 1.6;">
{actions_list}
    </ul>"""

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.subject}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 24px;">📧 Follow-up da Reunião</h1>
        {f'<p style="margin: 5px 0 0 0; opacity: 0.9;">{self.meeting_date}</p>' if self.meeting_date else ""}
    </div>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea;">
        <p style="margin: 0 0 10px 0;">{self.greeting}</p>
    </div>
    
    <h3 style="color: #2c3e50; margin-top: 25px;">📝 Resumo Executivo</h3>
    <p style="background: #e8f4f8; padding: 15px; border-radius: 6px; margin: 10px 0;">{self.summary}</p>
    
    {decisions_html}
    
    {actions_html}
    
    <h3 style="color: #27ae60; margin-top: 20px;">🚀 Próximos Passos</h3>
    <p style="background: #e8f5e8; padding: 15px; border-radius: 6px; margin: 10px 0;">{self.next_steps}</p>
    
    <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-top: 25px; border-top: 3px solid #667eea;">
        <p style="margin: 0;">{self.closing}</p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding: 15px; background: #f1f3f4; border-radius: 6px;">
        <p style="margin: 0; font-size: 12px; color: #666;">
            📄 Este email foi gerado automaticamente pelo <strong>ClareIA</strong><br>
            <em>Ferramenta inteligente para transcrição e análise de reuniões</em>
        </p>
    </div>
    
</body>
</html>"""

    def to_plain_text(self) -> str:
        """Converte o email para formato texto simples."""
        decisions_text = ""
        if self.key_decisions:
            decisions_list = "\n".join(f"  • {decision}" for decision in self.key_decisions)
            decisions_text = f"\n🎯 PRINCIPAIS DECISÕES:\n{decisions_list}\n"

        actions_text = ""
        if self.action_items:
            actions_list = "\n".join(f"  • {action}" for action in self.action_items)
            actions_text = f"\n📋 ITENS DE AÇÃO:\n{actions_list}\n"

        meeting_date_text = f"\nData da Reunião: {self.meeting_date}\n" if self.meeting_date else ""

        return f"""📧 FOLLOW-UP DA REUNIÃO
{"=" * 50}{meeting_date_text}
{self.greeting}

📝 RESUMO EXECUTIVO:
{self.summary}
{decisions_text}{actions_text}
🚀 PRÓXIMOS PASSOS:
{self.next_steps}

{self.closing}

---
📄 Este email foi gerado automaticamente pelo ClareIA
Ferramenta inteligente para transcrição e análise de reuniões"""
