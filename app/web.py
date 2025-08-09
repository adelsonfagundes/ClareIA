"""
ClareIA Web Interface
Interface web intuitiva para transcrição e sumarização de áudios com OpenAI.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

# Adiciona o diretório pai ao path para permitir imports do app
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import streamlit as st

# Importações do ClareIA
try:
    from app import __version__ as APP_VERSION
    from app.core.config import get_settings
    from app.core.summarizer import summarize_transcript
    from app.core.transcriber import transcribe_file
    from app.models.summary import MeetingSummary
    from app.models.transcript import Transcript
except ImportError:
    # Fallback para quando executado diretamente
    import __init__ as app_init
    from core.config import get_settings
    from core.summarizer import summarize_transcript
    from core.transcriber import transcribe_file
    from models.summary import MeetingSummary
    from models.transcript import Transcript

    APP_VERSION = getattr(app_init, "__version__", "0.1.0")


# Configuração da página (deve ser a primeira chamada Streamlit)
st.set_page_config(
    page_title="ClareIA - Transcriber & Summarizer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado para melhor aparência
st.markdown(
    """
    <style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def check_api_key() -> bool:
    """Verifica se a API key está configurada."""
    settings = get_settings()
    return bool(settings.openai_api_key)


def format_time_duration(seconds: float) -> str:
    """Formata duração em segundos para formato legível."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.0f}s"


def save_uploaded_file(uploaded_file) -> Path:
    """Salva arquivo uploaded temporariamente e retorna o caminho."""
    temp_dir = Path(tempfile.gettempdir()) / "clareia_uploads"
    temp_dir.mkdir(exist_ok=True)

    # Usa timestamp para evitar conflitos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = Path(uploaded_file.name).suffix
    temp_path = temp_dir / f"audio_{timestamp}{file_ext}"

    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return temp_path


def display_transcript(transcript: Transcript, key_suffix: str = "") -> None:
    """
    Exibe a transcrição de forma formatada.

    Args:
        transcript: Objeto Transcript para exibir
        key_suffix: Sufixo para tornar as keys únicas
    """
    with st.expander("📝 **Transcrição Completa**", expanded=True):
        # Métricas da transcrição
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Caracteres", f"{len(transcript.text):,}")
        with col2:
            st.metric("Palavras", f"{len(transcript.text.split()):,}")
        with col3:
            st.metric("Idioma", transcript.language.upper())

        # Texto da transcrição
        st.text_area(
            "Conteúdo",
            transcript.text,
            height=300,
            disabled=False,
            key=f"transcript_text_{key_suffix}",
            help="Você pode editar o texto aqui antes de gerar a ata",
        )

        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            st.info("💡 Use Ctrl+A para selecionar todo o texto")

        with col2:
            # Download como JSON
            transcript_json = json.dumps(transcript.model_dump(), ensure_ascii=False, indent=2)
            st.download_button(
                label="💾 Baixar JSON",
                data=transcript_json,
                file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key=f"download_transcript_{key_suffix}",
            )


def display_summary(summary: MeetingSummary, key_suffix: str = "") -> None:
    """
    Exibe o resumo/ata de forma estruturada.

    Args:
        summary: Objeto MeetingSummary para exibir
        key_suffix: Sufixo para tornar as keys únicas
    """
    with st.container():
        st.markdown("### 📊 Ata e Insights Gerados")

        # Título e resumo
        if summary.title:
            st.subheader(f"📌 {summary.title}")

        st.markdown("#### 📝 Resumo Executivo")
        st.info(summary.summary)

        # Layout em duas colunas
        col1, col2 = st.columns(2)

        with col1:
            # Pontos principais
            if summary.key_points:
                st.markdown("#### 🎯 Pontos Principais")
                for point in summary.key_points:
                    st.write(f"• {point}")

            # Decisões
            if summary.decisions:
                st.markdown("#### ✅ Decisões Tomadas")
                for decision in summary.decisions:
                    st.success(f"📍 {decision}")

        with col2:
            # Itens de ação
            if summary.action_items:
                st.markdown("#### 📋 Itens de Ação")
                for item in summary.action_items:
                    owner = f" **({item.owner})**" if item.owner else ""
                    due = f" - até {item.due_date}" if item.due_date else ""
                    st.warning(f"⚡ {item.description}{owner}{due}")

            # Insights
            if summary.insights:
                st.markdown("#### 💡 Insights")
                for insight in summary.insights:
                    st.info(f"💭 {insight}")

        # Downloads
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            # Download JSON
            summary_json = json.dumps(summary.model_dump(), ensure_ascii=False, indent=2)
            st.download_button(
                label="💾 Baixar Ata (JSON)",
                data=summary_json,
                file_name=f"ata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key=f"download_summary_json_{key_suffix}",
            )

        with col2:
            # Download Markdown (se o método existir)
            try:
                markdown_content = summary.to_markdown()
                st.download_button(
                    label="📄 Baixar Ata (Markdown)",
                    data=markdown_content,
                    file_name=f"ata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key=f"download_summary_md_{key_suffix}",
                )
            except AttributeError:
                # Se o método to_markdown não existir, cria um markdown básico
                markdown_content = f"""# {summary.title or "Ata da Reunião"}

## Resumo
{summary.summary}

## Pontos Principais
{chr(10).join("- " + p for p in summary.key_points)}

## Decisões
{chr(10).join("- " + d for d in summary.decisions)}

## Ações
{chr(10).join("- " + a.description for a in summary.action_items)}

## Insights
{chr(10).join("- " + i for i in summary.insights)}
"""
                st.download_button(
                    label="📄 Baixar Ata (Markdown)",
                    data=markdown_content,
                    file_name=f"ata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key=f"download_summary_md_{key_suffix}",
                )


def main():
    """Interface principal do Streamlit."""
    # Header
    st.title("🎙️ ClareIA - Transcriber & Summarizer")
    st.caption(f"v{APP_VERSION} | Ferramenta inteligente para transcrição e análise de reuniões")

    # Verifica API key
    if not check_api_key():
        st.error(
            "⚠️ **OPENAI_API_KEY não configurada!**\n\n"
            "Configure a variável de ambiente ou crie um arquivo `.env` com:\n"
            "```\nOPENAI_API_KEY=sua_chave_aqui\n```"
        )

        with st.expander("📚 Como configurar a API Key"):
            st.markdown("""
            ### Opção 1: Arquivo .env (Recomendado)
            1. Copie o arquivo `.env.example` para `.env`
            2. Edite o arquivo e adicione sua chave:
               ```
               OPENAI_API_KEY=sk-...
               ```
            3. Reinicie a aplicação
            
            ### Opção 2: Variável de Ambiente
            - **Windows (PowerShell):**
              ```powershell
              $env:OPENAI_API_KEY="sk-..."
              ```
            - **Linux/Mac:**
              ```bash
              export OPENAI_API_KEY="sk-..."
              ```
            """)
        st.stop()

    # Sidebar com configurações
    with st.sidebar:
        st.header("⚙️ Configurações")

        # Configurações de transcrição
        st.subheader("🎤 Transcrição")
        transcribe_model = st.selectbox(
            "Modelo",
            ["gpt-4o-transcribe", "whisper-1"],
            help="gpt-4o-transcribe é mais recente e preciso",
            key="sidebar_transcribe_model",
        )

        language = st.text_input(
            "Idioma (ISO 639-1)",
            value="pt",
            help="Código do idioma (pt para português)",
            key="sidebar_language",
        )

        # Ajusta formatos disponíveis baseado no modelo
        if transcribe_model == "gpt-4o-transcribe":
            format_options = ["json", "text"]
        else:
            format_options = ["json", "text", "verbose_json", "srt", "vtt"]

        response_format = st.selectbox(
            "Formato de Resposta",
            format_options,
            help="verbose_json/srt/vtt disponíveis apenas com whisper-1",
            key="sidebar_response_format",
        )

        prompt_hint = st.text_area(
            "Dica Contextual (opcional)",
            placeholder="Ex: Participantes: João, Maria\nTermos: OKR, NPS",
            help="Ajuda o modelo com nomes próprios e termos técnicos",
            height=100,
            key="sidebar_prompt_hint",
        )

        st.divider()

        # Configurações de sumarização
        st.subheader("📊 Sumarização")
        summary_model = st.selectbox(
            "Modelo",
            ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            help="gpt-4o-mini é rápido e eficiente",
            key="sidebar_summary_model",
        )

        temperature = st.slider(
            "Temperatura",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.1,
            help="Menor = mais focado, Maior = mais criativo",
            key="sidebar_temperature",
        )

        extra_context = st.text_area(
            "Contexto Adicional (opcional)",
            placeholder="Ex: Reunião de produto Q4\nParticipantes: Ana, Bruno",
            help="Informações extras para melhorar o resumo",
            height=100,
            key="sidebar_extra_context",
        )

        st.divider()

        # Botão para limpar sessão
        if st.button("🗑️ Limpar Sessão", key="clear_session"):
            for key in ["transcript", "summary", "processing_time", "summary_time"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Sessão limpa!")
            st.rerun()

        st.caption("💡 Dica: Use whisper-1 se precisar de timestamps")

    # Área principal com tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Transcrição", "📊 Análise & Ata", "📚 Ajuda"])

    with tab1:
        st.markdown("### Transcrição de Áudio")
        st.markdown("Faça upload de um arquivo de áudio para transcrever")

        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "Selecione um arquivo de áudio",
            type=["mp3", "wav", "m4a"],
            help="Formatos suportados: MP3, WAV, M4A (máx. 25MB)",
            key="audio_uploader",
        )

        if uploaded_file is not None:
            # Informações do arquivo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Arquivo", uploaded_file.name)
            with col2:
                size_mb = uploaded_file.size / (1024 * 1024)
                st.metric("Tamanho", f"{size_mb:.2f} MB")
            with col3:
                file_ext = Path(uploaded_file.name).suffix.upper()
                st.metric("Formato", file_ext)

            # Botão de transcrição
            if st.button("🚀 Iniciar Transcrição", type="primary", use_container_width=True, key="start_transcription"):
                with st.spinner("Transcrevendo áudio... Isso pode levar alguns minutos."):
                    try:
                        # Salva arquivo temporariamente
                        temp_path = save_uploaded_file(uploaded_file)

                        # Transcreve
                        start_time = datetime.now()
                        transcript = transcribe_file(
                            str(temp_path),
                            model=transcribe_model,
                            language=language,
                            response_format=response_format,
                            prompt=prompt_hint if prompt_hint else None,
                        )
                        processing_time = (datetime.now() - start_time).total_seconds()

                        # Armazena no session state
                        st.session_state["transcript"] = transcript
                        st.session_state["processing_time"] = processing_time

                        # Remove arquivo temporário
                        try:
                            temp_path.unlink(missing_ok=True)
                        except:
                            pass  # Ignora erros ao deletar temporário

                        st.success(f"✅ Transcrição concluída em {format_time_duration(processing_time)}!")

                        # Exibe transcrição
                        display_transcript(transcript, key_suffix="tab1_new")

                    except Exception as e:
                        st.error(f"❌ Erro na transcrição: {str(e)}")
                        if st.checkbox("Mostrar detalhes do erro", key="error_details_transcription"):
                            st.exception(e)

        # Se já existe transcrição na sessão, mostra
        elif "transcript" in st.session_state:
            st.info("ℹ️ Transcrição anterior disponível")
            display_transcript(st.session_state["transcript"], key_suffix="tab1_existing")

    with tab2:
        st.markdown("### Geração de Ata e Insights")
        st.markdown("Analise a transcrição e gere uma ata estruturada")

        if "transcript" not in st.session_state:
            st.warning(
                "⚠️ Nenhuma transcrição disponível. "
                "Faça upload e transcreva um áudio primeiro na aba 'Upload & Transcrição'."
            )
        else:
            transcript = st.session_state["transcript"]

            # Preview da transcrição
            with st.expander("📝 Preview da Transcrição", expanded=False):
                preview_text = transcript.text[:1000]
                if len(transcript.text) > 1000:
                    preview_text += "..."
                st.text(preview_text)

            # Botão para gerar resumo
            if st.button("🎯 Gerar Ata e Insights", type="primary", use_container_width=True, key="generate_summary"):
                with st.spinner("Analisando transcrição e gerando insights..."):
                    try:
                        start_time = datetime.now()
                        summary = summarize_transcript(
                            transcript,
                            model=summary_model,
                            temperature=temperature,
                            extra_context=extra_context if extra_context else None,
                        )
                        processing_time = (datetime.now() - start_time).total_seconds()

                        # Armazena no session state
                        st.session_state["summary"] = summary
                        st.session_state["summary_time"] = processing_time

                        st.success(f"✅ Ata gerada em {format_time_duration(processing_time)}!")

                        # Exibe resumo
                        display_summary(summary, key_suffix="tab2_new")

                    except Exception as e:
                        st.error(f"❌ Erro ao gerar ata: {str(e)}")
                        if st.checkbox("Mostrar detalhes do erro", key="error_details_summary"):
                            st.exception(e)

            # Se já existe resumo na sessão, mostra
            if "summary" in st.session_state and st.session_state.get("summary"):
                st.divider()
                st.info("ℹ️ Última ata gerada:")
                display_summary(st.session_state["summary"], key_suffix="tab2_existing")

    with tab3:
        st.markdown("### 📚 Ajuda e Documentação")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                """
                #### 🎯 Como Usar
                
                1. **Configure as opções** no painel lateral
                2. **Faça upload** de um arquivo de áudio
                3. **Transcreva** o áudio para texto
                4. **Gere a ata** com insights estruturados
                5. **Baixe** os resultados em JSON ou Markdown
                
                #### 📝 Formatos Suportados
                
                **Áudio:**
                - MP3 (recomendado)
                - WAV
                - M4A
                
                **Tamanho máximo:** 25MB
                
                #### 🚀 Executando a Aplicação
                
                ```bash
                # Opção 1 - Script auxiliar
                python run_web.py
                
                # Opção 2 - Comando direto
                streamlit run app/web.py
                ```
                """
            )

        with col2:
            st.markdown(
                """
                #### 🤖 Modelos Disponíveis
                
                **Transcrição:**
                - `gpt-4o-transcribe`: Mais recente e preciso
                - `whisper-1`: Suporta timestamps e legendas
                
                **Sumarização:**
                - `gpt-4o-mini`: Rápido e eficiente
                - `gpt-4o`: Mais capaz
                - `gpt-3.5-turbo`: Alternativa econômica
                
                #### 💡 Dicas
                
                - Use **dicas contextuais** para melhorar nomes próprios
                - **Temperatura baixa** (0.2) para resumos objetivos
                - **whisper-1** se precisar de timestamps
                - **Limpe a sessão** se quiser começar do zero
                
                #### 🔧 Solução de Problemas
                
                **API Key não encontrada:**
                - Verifique o arquivo `.env`
                - Reinicie a aplicação após configurar
                
                **Erro de transcrição:**
                - Verifique o formato do arquivo
                - Confirme que o arquivo tem menos de 25MB
                """
            )

        st.divider()

        # Estatísticas da sessão
        if "transcript" in st.session_state or "summary" in st.session_state:
            st.markdown("#### 📊 Estatísticas da Sessão")

            col1, col2, col3, col4 = st.columns(4)

            if "transcript" in st.session_state:
                with col1:
                    st.metric(
                        "Transcrição",
                        "✅ Completa",
                        f"{st.session_state.get('processing_time', 0):.1f}s",
                    )
                with col2:
                    st.metric(
                        "Caracteres",
                        f"{len(st.session_state['transcript'].text):,}",
                    )

            if "summary" in st.session_state and st.session_state.get("summary"):
                with col3:
                    st.metric(
                        "Ata",
                        "✅ Gerada",
                        f"{st.session_state.get('summary_time', 0):.1f}s",
                    )
                with col4:
                    summary = st.session_state["summary"]
                    total_items = len(summary.decisions) + len(summary.action_items) + len(summary.insights)
                    st.metric("Items Extraídos", total_items)

        # Footer
        st.divider()
        st.caption(
            f"ClareIA v{APP_VERSION} | "
            "Desenvolvido com ❤️ usando Python e Streamlit | "
            "[GitHub](https://github.com/adelsonfagundes/ClareIA)"
        )


# Executa a aplicação
if __name__ == "__main__":
    main()
