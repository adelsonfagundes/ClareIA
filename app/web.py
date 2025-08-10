"""
ClareIA Web Interface
Interface web intuitiva para transcrição e sumarização de áudios com OpenAI.
"""

from __future__ import annotations

import contextlib
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

# Adiciona o diretório pai ao path para permitir imports do app
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import streamlit as st  # noqa: E402

if TYPE_CHECKING:
    from models.summary import MeetingSummary
    from models.transcript import Transcript
    from streamlit.runtime.uploaded_file_manager import UploadedFile

# Importações do ClareIA
try:
    from app import __version__
    from app.components.audio_player import create_simple_audio_player, create_synchronized_player
    from app.core.config import get_settings
    from app.core.summarizer import summarize_transcript
    from app.core.transcriber import transcribe_file

    APP_VERSION = __version__
except ImportError:
    # Fallback para quando executado diretamente
    import __init__ as app_init
    from components.audio_player import create_simple_audio_player, create_synchronized_player
    from core.config import get_settings
    from core.summarizer import summarize_transcript
    from core.transcriber import transcribe_file

    APP_VERSION = getattr(app_init, "__version__", "0.1.0")

# Constantes
SECONDS_PER_MINUTE = 60
PREVIEW_LENGTH = 1000

# Configuração da página (deve ser a primeira chamada Streamlit)
st.set_page_config(
    page_title="ClareIA - Transcriber & Summarizer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado - Forçar largura total para o player
st.markdown(
    """
    <style>
    /* Container principal sem limitações */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Forçar largura total para componentes HTML */
    div[data-testid="stHtml"] {
        width: 100% !important;
    }
    
    /* Iframe do componente sem limitações */
    iframe[title="st.components.v1.html"] {
        width: 100% !important;
        border: none;
    }
    
    /* Container do iframe */
    .element-container:has(iframe[title="st.components.v1.html"]) {
        width: 100% !important;
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Estilos gerais da aplicação */
    .stApp {
        max-width: 100% !important;
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
    
    /* Sidebar com largura fixa */
    section[data-testid="stSidebar"] {
        width: 300px !important;
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
    if seconds < SECONDS_PER_MINUTE:
        return f"{seconds:.1f}s"
    minutes = int(seconds // SECONDS_PER_MINUTE)
    secs = seconds % SECONDS_PER_MINUTE
    return f"{minutes}m {secs:.0f}s"


def save_uploaded_file(uploaded_file: UploadedFile) -> Path:
    """Salva arquivo uploaded temporariamente e retorna o caminho."""
    temp_dir = Path(tempfile.gettempdir()) / "clareia_uploads"
    temp_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    file_ext = Path(uploaded_file.name).suffix
    temp_path = temp_dir / f"audio_{timestamp}{file_ext}"

    with temp_path.open("wb") as f:
        f.write(uploaded_file.getbuffer())

    return temp_path


def display_transcript(transcript: Transcript, audio_path: Path | None = None, key_suffix: str = "") -> None:
    """Exibe a transcrição de forma formatada com player sincronizado opcional."""

    # Se temos um caminho de áudio e timestamps, mostrar player sincronizado
    if audio_path and transcript.segments:
        st.markdown("### 🎵 Player Sincronizado")
        st.info("💡 Clique em qualquer trecho da transcrição para pular para aquele momento no áudio!")

        # Player sincronizado com largura total
        create_synchronized_player(audio_path, transcript, height=750)

        st.divider()
    elif audio_path:
        st.markdown("### 🎵 Player de Áudio")
        create_simple_audio_player(audio_path)
        st.divider()

    with st.expander("📝 **Transcrição Completa em Texto**", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Caracteres", f"{len(transcript.text):,}")
        with col2:
            st.metric("Palavras", f"{len(transcript.text.split()):,}")
        with col3:
            st.metric("Idioma", transcript.language.upper())

        st.text_area(
            "Conteúdo",
            transcript.text,
            height=300,
            disabled=False,
            key=f"transcript_text_{key_suffix}",
            help="Você pode editar o texto aqui antes de gerar a ata",
        )

        col1, col2 = st.columns(2)
        with col1:
            if transcript.segments:
                st.success(f"✅ {len(transcript.segments)} segmentos com timestamps disponíveis")
            else:
                st.info("💡 Use whisper-1 com verbose_json para obter timestamps")

        with col2:
            transcript_json = json.dumps(transcript.model_dump(), ensure_ascii=False, indent=2)
            timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="💾 Baixar JSON",
                data=transcript_json,
                file_name=f"transcript_{timestamp}.json",
                mime="application/json",
                key=f"download_transcript_{key_suffix}",
            )


def display_summary(summary: MeetingSummary, key_suffix: str = "") -> None:
    """Exibe o resumo/ata de forma estruturada."""
    with st.container():
        st.markdown("### 📊 Ata e Insights Gerados")

        if summary.title:
            st.subheader(f"📌 {summary.title}")

        st.markdown("#### 📝 Resumo Executivo")
        st.info(summary.summary)

        col1, col2 = st.columns(2)

        with col1:
            if summary.key_points:
                st.markdown("#### 🎯 Pontos Principais")
                for point in summary.key_points:
                    st.write(f"• {point}")

            if summary.decisions:
                st.markdown("#### ✅ Decisões Tomadas")
                for decision in summary.decisions:
                    st.success(f"📍 {decision}")

        with col2:
            if summary.action_items:
                st.markdown("#### 📋 Itens de Ação")
                for item in summary.action_items:
                    owner = f" **({item.owner})**" if item.owner else ""
                    due = f" - até {item.due_date}" if item.due_date else ""
                    st.warning(f"⚡ {item.description}{owner}{due}")

            if summary.insights:
                st.markdown("#### 💡 Insights")
                for insight in summary.insights:
                    st.info(f"💭 {insight}")

        st.divider()
        col1, col2 = st.columns(2)

        timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")

        with col1:
            summary_json = json.dumps(summary.model_dump(), ensure_ascii=False, indent=2)
            st.download_button(
                label="💾 Baixar Ata (JSON)",
                data=summary_json,
                file_name=f"ata_{timestamp}.json",
                mime="application/json",
                key=f"download_summary_json_{key_suffix}",
            )

        with col2:
            try:
                markdown_content = summary.to_markdown()
            except AttributeError:
                markdown_content = _create_markdown_from_summary(summary)

            st.download_button(
                label="📄 Baixar Ata (Markdown)",
                data=markdown_content,
                file_name=f"ata_{timestamp}.md",
                mime="text/markdown",
                key=f"download_summary_md_{key_suffix}",
            )


def _create_markdown_from_summary(summary: MeetingSummary) -> str:
    """Cria markdown a partir do resumo."""
    return f"""# {summary.title or "Ata da Reunião"}

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


def _handle_transcription(uploaded_file: UploadedFile, config: dict) -> None:
    """Processa a transcrição do arquivo."""
    with st.spinner("Transcrevendo áudio... Isso pode levar alguns minutos."):
        try:
            temp_path = save_uploaded_file(uploaded_file)

            start_time = datetime.now(tz=UTC)
            transcript = transcribe_file(
                str(temp_path),
                model=config["model"],
                language=config["language"],
                response_format=config["format"],
                prompt=config.get("prompt"),
            )
            processing_time = (datetime.now(tz=UTC) - start_time).total_seconds()

            st.session_state["transcript"] = transcript
            st.session_state["processing_time"] = processing_time
            st.session_state["audio_path"] = temp_path

            st.success(f"✅ Transcrição concluída em {format_time_duration(processing_time)}!")

            # Exibir com player sincronizado se disponível
            display_transcript(transcript, audio_path=temp_path, key_suffix="tab1_new")

        except Exception as e:
            st.error(f"❌ Erro na transcrição: {e!s}")
            if st.checkbox("Mostrar detalhes do erro", key="error_details_transcription"):
                st.exception(e)


def _handle_summary_generation(transcript: Transcript, config: dict) -> None:
    """Gera o resumo da transcrição."""
    with st.spinner("Analisando transcrição e gerando insights..."):
        try:
            start_time = datetime.now(tz=UTC)
            summary = summarize_transcript(
                transcript,
                model=config["model"],
                temperature=config["temperature"],
                extra_context=config.get("context"),
            )
            processing_time = (datetime.now(tz=UTC) - start_time).total_seconds()

            st.session_state["summary"] = summary
            st.session_state["summary_time"] = processing_time

            st.success(f"✅ Ata gerada em {format_time_duration(processing_time)}!")
            display_summary(summary, key_suffix="tab2_new")

        except Exception as e:
            st.error(f"❌ Erro ao gerar ata: {e!s}")
            if st.checkbox("Mostrar detalhes do erro", key="error_details_summary"):
                st.exception(e)


def main() -> None:
    """Interface principal do Streamlit."""
    st.title("🎙️ ClareIA - Transcriber & Summarizer")
    st.caption(f"v{APP_VERSION} | Ferramenta inteligente para transcrição e análise de reuniões")

    if not check_api_key():
        _show_api_key_error()
        return

    config = _setup_sidebar()
    _show_main_tabs(config)


def _show_api_key_error() -> None:
    """Mostra erro de API key não configurada."""
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


def _setup_sidebar() -> dict:
    """Configura a sidebar e retorna configurações."""
    config = {}

    with st.sidebar:
        st.header("⚙️ Configurações")

        st.subheader("🎤 Transcrição")
        config["transcribe_model"] = st.selectbox(
            "Modelo",
            ["whisper-1", "gpt-4o-mini-transcribe"],
            help="whisper-1 suporta timestamps para player sincronizado",
            key="sidebar_transcribe_model",
        )

        config["language"] = st.text_input(
            "Idioma (ISO 639-1)",
            value="pt",
            help="Código do idioma (pt para português)",
            key="sidebar_language",
        )

        format_options = (
            ["json", "text"]
            if config["transcribe_model"] == "gpt-4o-mini-transcribe"
            else ["verbose_json", "json", "text", "srt", "vtt"]
        )

        # Selecionar verbose_json por padrão para whisper-1
        default_format = "verbose_json" if config["transcribe_model"] == "whisper-1" else "json"

        config["response_format"] = st.selectbox(
            "Formato de Resposta",
            format_options,
            index=format_options.index(default_format) if default_format in format_options else 0,
            help="Use 'verbose_json' com whisper-1 para habilitar player sincronizado",
            key="sidebar_response_format",
        )

        # Aviso sobre player sincronizado
        if config["transcribe_model"] == "whisper-1" and config["response_format"] == "verbose_json":
            st.success("✅ Player sincronizado será habilitado!")
        elif config["transcribe_model"] == "whisper-1":
            st.info("💡 Use 'verbose_json' para habilitar player sincronizado")
        else:
            st.warning("⚠️ Player sincronizado requer whisper-1 + verbose_json")

        config["prompt_hint"] = st.text_area(
            "Dica Contextual (opcional)",
            placeholder="Ex: Participantes: João, Maria\nTermos: OKR, NPS",
            help="Ajuda o modelo com nomes próprios e termos técnicos",
            height=100,
            key="sidebar_prompt_hint",
        )

        st.divider()

        st.subheader("📊 Sumarização")
        config["summary_model"] = st.selectbox(
            "Modelo",
            ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            help="gpt-4o-mini é rápido e eficiente",
            key="sidebar_summary_model",
        )

        config["temperature"] = st.slider(
            "Temperatura",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.1,
            help="Menor = mais focado, Maior = mais criativo",
            key="sidebar_temperature",
        )

        config["extra_context"] = st.text_area(
            "Contexto Adicional (opcional)",
            placeholder="Ex: Reunião de produto Q4\nParticipantes: Ana, Bruno",
            help="Informações extras para melhorar o resumo",
            height=100,
            key="sidebar_extra_context",
        )

        st.divider()

        if st.button("🗑️ Limpar Sessão", key="clear_session"):
            for key in ["transcript", "summary", "processing_time", "summary_time", "audio_path"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Sessão limpa!")
            st.rerun()

        st.caption("🎯 Player sincronizado: whisper-1 + verbose_json")

    return config


def _show_main_tabs(config: dict) -> None:
    """Mostra as tabs principais da aplicação."""
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Transcrição", "📊 Análise & Ata", "📚 Ajuda"])

    with tab1:
        _show_transcription_tab(config)

    with tab2:
        _show_summary_tab(config)

    with tab3:
        _show_help_tab()


def _show_transcription_tab(config: dict) -> None:
    """Mostra a tab de transcrição."""
    st.markdown("### Transcrição de Áudio")
    st.markdown("Faça upload de um arquivo de áudio para transcrever")

    uploaded_file = st.file_uploader(
        "Selecione um arquivo de áudio",
        type=["mp3", "wav", "m4a"],
        help="Formatos suportados: MP3, WAV, M4A (máx. 25MB)",
        key="audio_uploader",
    )

    if uploaded_file is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Arquivo", uploaded_file.name)
        with col2:
            size_mb = uploaded_file.size / (1024 * 1024)
            st.metric("Tamanho", f"{size_mb:.2f} MB")
        with col3:
            file_ext = Path(uploaded_file.name).suffix.upper()
            st.metric("Formato", file_ext)

        if st.button("🚀 Iniciar Transcrição", type="primary", use_container_width=True, key="start_transcription"):
            transcription_config = {
                "model": config["transcribe_model"],
                "language": config["language"],
                "format": config["response_format"],
                "prompt": config["prompt_hint"] if config["prompt_hint"] else None,
            }
            _handle_transcription(uploaded_file, transcription_config)

    elif "transcript" in st.session_state:
        st.info("📋 Transcrição anterior disponível")
        audio_path = st.session_state.get("audio_path")
        display_transcript(st.session_state["transcript"], audio_path=audio_path, key_suffix="tab1_existing")


def _show_summary_tab(config: dict) -> None:
    """Mostra a tab de geração de resumo."""
    st.markdown("### Geração de Ata e Insights")
    st.markdown("Analise a transcrição e gere uma ata estruturada")

    if "transcript" not in st.session_state:
        st.warning(
            "⚠️ Nenhuma transcrição disponível. "
            "Faça upload e transcreva um áudio primeiro na aba 'Upload & Transcrição'."
        )
        return

    transcript = st.session_state["transcript"]

    with st.expander("📝 Preview da Transcrição", expanded=False):
        preview_text = transcript.text[:PREVIEW_LENGTH]
        if len(transcript.text) > PREVIEW_LENGTH:
            preview_text += "..."
        st.text(preview_text)

    if st.button("🎯 Gerar Ata e Insights", type="primary", use_container_width=True, key="generate_summary"):
        summary_config = {
            "model": config["summary_model"],
            "temperature": config["temperature"],
            "context": config["extra_context"] if config["extra_context"] else None,
        }
        _handle_summary_generation(transcript, summary_config)

    if "summary" in st.session_state and st.session_state.get("summary"):
        st.divider()
        st.info("📄 Última ata gerada:")
        display_summary(st.session_state["summary"], key_suffix="tab2_existing")


def _show_help_tab() -> None:
    """Mostra a tab de ajuda."""
    st.markdown("### 📚 Ajuda e Documentação")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 🎯 Como Usar

        1. **Configure as opções** no painel lateral
        2. **Faça upload** de um arquivo de áudio
        3. **Transcreva** o áudio para texto
        4. **Gere a ata** com insights estruturados
        5. **Baixe** os resultados em JSON ou Markdown

        #### 🎵 Player Sincronizado

        **Para ativar o player sincronizado:**
        1. Escolha modelo **whisper-1**
        2. Selecione formato **verbose_json**
        3. Faça a transcrição
        4. O player aparecerá automaticamente!

        **Recursos do player:**
        - Clique em qualquer trecho para pular
        - Controle de velocidade (0.5x a 2x)
        - Destaque automático do texto atual
        - Scroll automático suave
        - Barra de progresso clicável

        #### 📝 Formatos Suportados

        **Áudio:**
        - MP3 (recomendado)
        - WAV
        - M4A

        **Tamanho máximo:** 25MB
        """)

    with col2:
        st.markdown("""
        #### 🤖 Modelos Disponíveis

        **Transcrição:**
        - `whisper-1`: **Recomendado** - Suporta timestamps
        - `gpt-4o-mini-transcribe`: Mais recente, sem timestamps

        **Formatos de resposta:**
        - `verbose_json`: **Habilita player sincronizado**
        - `json`: Transcrição simples
        - `text`: Apenas texto
        - `srt/vtt`: Legendas

        **Sumarização:**
        - `gpt-4o-mini`: Rápido e eficiente
        - `gpt-4o`: Mais capaz
        - `gpt-3.5-turbo`: Alternativa econômica

        #### 💡 Dicas

        - **Player sincronizado** = whisper-1 + verbose_json
        - Use **dicas contextuais** para nomes próprios
        - **Temperatura baixa** (0.2) para resumos objetivos
        - **Limpe a sessão** para começar do zero

        #### 🔧 Solução de Problemas

        **Player não aparece?**
        - Use whisper-1 + verbose_json
        - Verifique se o áudio foi processado

        **Player ainda estreito?**
        - Faça hard refresh (Ctrl+F5)
        - Verifique zoom do navegador (100%)
        - Teste em aba anônima
        """)

    st.divider()
    _show_session_stats()

    st.divider()
    st.caption(
        f"ClareIA v{APP_VERSION} | "
        "Desenvolvido com ❤️ usando Python e Streamlit | "
        "[GitHub](https://github.com/adelsonfagundes/ClareIA)"
    )


def _show_session_stats() -> None:
    """Mostra estatísticas da sessão."""
    if "transcript" not in st.session_state and "summary" not in st.session_state:
        return

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
            transcript = st.session_state["transcript"]
            segments_info = f"{len(transcript.segments)} segs" if transcript.segments else "Sem timestamps"
            st.metric("Segmentos", segments_info)

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


if __name__ == "__main__":
    main()
