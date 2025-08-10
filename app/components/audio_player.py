"""Componente de player de áudio sincronizado com transcrição."""

from __future__ import annotations

import base64
import json
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st
import streamlit.components.v1 as components

if TYPE_CHECKING:
    from app.models.transcript import Transcript


def create_synchronized_player(
    audio_path: str | Path,
    transcript: Transcript,
    height: int = 600,
) -> None:
    """
    Cria um player de áudio sincronizado com a transcrição.

    Args:
        audio_path: Caminho para o arquivo de áudio
        transcript: Objeto Transcript com segments contendo timestamps
        height: Altura do componente em pixels
    """
    if not transcript.segments:
        st.warning(
            "⚠️ Esta transcrição não possui timestamps. Use o modelo 'whisper-1' com formato 'verbose_json' para habilitar sincronização."
        )
        return

    # Converter Path para string se necessário
    audio_path = str(audio_path) if isinstance(audio_path, Path) else audio_path

    # Verificar se o arquivo existe
    if not Path(audio_path).exists():
        st.error(f"❌ Arquivo de áudio não encontrado: {audio_path}")
        return

    # Ler o arquivo de áudio e converter para base64
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    audio_base64 = base64.b64encode(audio_bytes).decode()

    # Determinar o tipo MIME baseado na extensão
    audio_ext = Path(audio_path).suffix.lower()
    mime_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".webm": "audio/webm",
    }
    audio_mime = mime_types.get(audio_ext, "audio/mpeg")

    # Preparar dados dos segmentos
    segments_data = []
    for seg in transcript.segments:
        segments_data.append(
            {
                "start": seg.start or 0,
                "end": seg.end or 0,
                "text": seg.text,
                "id": f"seg-{len(segments_data)}",
            }
        )

    # Gerar ID único para o componente
    component_id = f"audio-player-{uuid.uuid4().hex[:8]}"

    # HTML e JavaScript para o player sincronizado
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f7f7f7;
                padding: 20px;
            }}
            
            .player-container {{
                max-width: 100%;
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .audio-controls {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            
            audio {{
                width: 100%;
                outline: none;
            }}
            
            .time-display {{
                color: white;
                text-align: center;
                margin-top: 10px;
                font-size: 14px;
                opacity: 0.9;
            }}
            
            .transcript-container {{
                padding: 20px;
                max-height: 400px;
                overflow-y: auto;
                scroll-behavior: smooth;
            }}
            
            .segment {{
                padding: 12px 16px;
                margin: 8px 0;
                border-radius: 8px;
                transition: all 0.3s ease;
                cursor: pointer;
                line-height: 1.6;
                border-left: 3px solid transparent;
            }}
            
            .segment:hover {{
                background: #f0f0f0;
                transform: translateX(4px);
            }}
            
            .segment.active {{
                background: linear-gradient(90deg, #667eea15 0%, #764ba215 100%);
                border-left-color: #667eea;
                transform: translateX(8px);
                font-weight: 500;
            }}
            
            .segment.played {{
                opacity: 0.6;
            }}
            
            .segment-time {{
                display: inline-block;
                font-size: 11px;
                color: #666;
                margin-right: 8px;
                font-family: 'Courier New', monospace;
                background: #f0f0f0;
                padding: 2px 6px;
                border-radius: 4px;
            }}
            
            .progress-bar {{
                height: 4px;
                background: rgba(255,255,255,0.3);
                border-radius: 2px;
                overflow: hidden;
                margin-top: 10px;
            }}
            
            .progress-fill {{
                height: 100%;
                background: white;
                border-radius: 2px;
                width: 0%;
                transition: width 0.1s linear;
            }}
            
            .controls-row {{
                display: flex;
                align-items: center;
                gap: 15px;
                margin-top: 10px;
            }}
            
            .speed-control {{
                color: white;
                background: rgba(255,255,255,0.2);
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 12px;
            }}
            
            .speed-control:hover {{
                background: rgba(255,255,255,0.3);
            }}
            
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
                100% {{ opacity: 1; }}
            }}
            
            .segment.active {{
                animation: pulse 2s infinite;
            }}
        </style>
    </head>
    <body>
        <div class="player-container">
            <div class="audio-controls">
                <audio id="audioPlayer" controls>
                    <source src="data:{audio_mime};base64,{audio_base64}" type="{audio_mime}">
                    Seu navegador não suporta o elemento de áudio.
                </audio>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="time-display" id="timeDisplay">00:00 / 00:00</div>
                <div class="controls-row">
                    <button class="speed-control" onclick="changeSpeed(0.5)">0.5x</button>
                    <button class="speed-control" onclick="changeSpeed(0.75)">0.75x</button>
                    <button class="speed-control" onclick="changeSpeed(1)">1x</button>
                    <button class="speed-control" onclick="changeSpeed(1.25)">1.25x</button>
                    <button class="speed-control" onclick="changeSpeed(1.5)">1.5x</button>
                    <button class="speed-control" onclick="changeSpeed(2)">2x</button>
                </div>
            </div>
            <div class="transcript-container" id="transcriptContainer">
                <!-- Segments serão inseridos aqui -->
            </div>
        </div>
        
        <script>
            const segments = {json.dumps(segments_data)};
            const audio = document.getElementById('audioPlayer');
            const transcriptContainer = document.getElementById('transcriptContainer');
            const timeDisplay = document.getElementById('timeDisplay');
            const progressFill = document.getElementById('progressFill');
            
            // Formatar tempo
            function formatTime(seconds) {{
                const mins = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${{mins.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
            }}
            
            // Renderizar segmentos
            function renderSegments() {{
                transcriptContainer.innerHTML = segments.map(seg => `
                    <div class="segment" 
                         id="${{seg.id}}" 
                         data-start="${{seg.start}}" 
                         data-end="${{seg.end}}"
                         onclick="seekToSegment(${{seg.start}})">
                        <span class="segment-time">${{formatTime(seg.start)}}</span>
                        <span class="segment-text">${{seg.text}}</span>
                    </div>
                `).join('');
            }}
            
            // Pular para segmento
            function seekToSegment(time) {{
                audio.currentTime = time;
                audio.play();
            }}
            
            // Mudar velocidade
            function changeSpeed(rate) {{
                audio.playbackRate = rate;
            }}
            
            // Atualizar segmento ativo
            function updateActiveSegment() {{
                const currentTime = audio.currentTime;
                const allSegments = document.querySelectorAll('.segment');
                
                allSegments.forEach(seg => {{
                    const start = parseFloat(seg.dataset.start);
                    const end = parseFloat(seg.dataset.end);
                    
                    seg.classList.remove('active');
                    
                    if (currentTime >= start && currentTime < end) {{
                        seg.classList.add('active');
                        // Scroll suave para o segmento ativo
                        seg.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }}
                    
                    if (currentTime > end) {{
                        seg.classList.add('played');
                    }} else {{
                        seg.classList.remove('played');
                    }}
                }});
                
                // Atualizar display de tempo
                timeDisplay.textContent = `${{formatTime(currentTime)}} / ${{formatTime(audio.duration || 0)}}`;
                
                // Atualizar barra de progresso
                if (audio.duration) {{
                    progressFill.style.width = `${{(currentTime / audio.duration) * 100}}%`;
                }}
            }}
            
            // Event listeners
            audio.addEventListener('timeupdate', updateActiveSegment);
            audio.addEventListener('loadedmetadata', () => {{
                timeDisplay.textContent = `00:00 / ${{formatTime(audio.duration)}}`;
            }});
            
            // Inicializar
            renderSegments();
        </script>
    </body>
    </html>
    """

    # Renderizar o componente
    components.html(html_content, height=height, scrolling=True)


def create_simple_audio_player(audio_path: str | Path) -> None:
    """
    Cria um player de áudio simples para transcrições sem timestamps.

    Args:
        audio_path: Caminho para o arquivo de áudio
    """
    audio_path = Path(audio_path) if isinstance(audio_path, str) else audio_path

    if not audio_path.exists():
        st.error(f"❌ Arquivo de áudio não encontrado: {audio_path}")
        return

    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    st.audio(audio_bytes, format=f"audio/{audio_path.suffix[1:]}")
