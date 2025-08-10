"""Componente de player de áudio sincronizado com transcrição."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st
import streamlit.components.v1 as components

if TYPE_CHECKING:
    from app.models.transcript import Transcript


def create_synchronized_player(
    audio_path: str | Path,
    transcript: Transcript,
    height: int = 750,
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

    # Preparar dados dos segmentos com conversão segura
    segments_data = []
    for i, seg in enumerate(transcript.segments):
        segments_data.append(
            {
                "start": float(seg.start or 0.0),
                "end": float(seg.end or (seg.start or 0.0) + 0.01),
                "text": seg.text,
                "id": f"seg-{i}",
            }
        )

    # HTML e JavaScript para o player sincronizado
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            html, body {{
                width: 100%;
                height: 100%;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: #f0f2f6;
            }}
            
            .player-container {{
                width: 100%;
                max-width: 100%;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                overflow: hidden;
                display: flex;
                flex-direction: column;
                height: 100%;
            }}
            
            .audio-section {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 24px;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
                flex-shrink: 0;
            }}
            
            .audio-wrapper {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 16px;
                backdrop-filter: blur(10px);
            }}
            
            audio {{
                width: 100%;
                height: 54px;
                outline: none;
                filter: invert(1);
                opacity: 0.9;
            }}
            
            .controls-section {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 16px;
                flex-wrap: wrap;
                gap: 12px;
            }}
            
            .time-display {{
                color: white;
                font-size: 14px;
                font-weight: 500;
                background: rgba(255, 255, 255, 0.15);
                padding: 8px 16px;
                border-radius: 25px;
                min-width: 130px;
                text-align: center;
            }}
            
            .speed-controls {{
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }}
            
            .speed-control {{
                color: white;
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                padding: 8px 16px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                transition: all 0.2s ease;
                min-width: 50px;
                text-align: center;
            }}
            
            .speed-control:hover {{
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-1px);
            }}
            
            .speed-control.active {{
                background: white;
                color: #667eea;
                border-color: white;
            }}
            
            .progress-bar {{
                height: 6px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
                overflow: hidden;
                margin-top: 16px;
                cursor: pointer;
                position: relative;
            }}
            
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, #ffffff 0%, #f0f0ff 100%);
                border-radius: 3px;
                width: 0%;
                transition: width 0.1s linear;
                box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
            }}
            
            .progress-bar:hover {{
                height: 8px;
            }}
            
            .transcript-section {{
                flex: 1;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                background: #fafbfc;
            }}
            
            .transcript-header {{
                padding: 20px 24px;
                background: white;
                border-bottom: 2px solid #e1e4e8;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-shrink: 0;
            }}
            
            .transcript-title {{
                font-size: 20px;
                font-weight: 700;
                color: #24292e;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .segment-count {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
            }}
            
            .transcript-container {{
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                scroll-behavior: smooth;
            }}
            
            .transcript-container::-webkit-scrollbar {{
                width: 10px;
            }}
            
            .transcript-container::-webkit-scrollbar-track {{
                background: #f0f2f6;
                border-radius: 5px;
            }}
            
            .transcript-container::-webkit-scrollbar-thumb {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 5px;
            }}
            
            .segment {{
                padding: 18px 24px;
                margin: 16px 0;
                background: white;
                border-radius: 16px;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                cursor: pointer;
                line-height: 1.8;
                border: 2px solid transparent;
                position: relative;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }}
            
            .segment:hover {{
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
                transform: translateY(-2px);
                border-color: #e1e4e8;
            }}
            
            .segment.active {{
                background: linear-gradient(135deg, #667eea12 0%, #764ba212 100%);
                border-color: #667eea;
                box-shadow: 0 8px 30px rgba(102, 126, 234, 0.25);
                transform: translateY(-4px) scale(1.02);
            }}
            
            .segment.played {{
                opacity: 0.6;
                background: #f8f9fa;
            }}
            
            .segment-content {{
                display: flex;
                gap: 20px;
                align-items: flex-start;
            }}
            
            .segment-time {{
                display: inline-flex;
                align-items: center;
                font-size: 13px;
                color: #586069;
                font-family: 'SF Mono', Monaco, 'Courier New', monospace;
                background: #f0f2f6;
                padding: 6px 14px;
                border-radius: 8px;
                font-weight: 600;
                white-space: nowrap;
                min-width: 80px;
                justify-content: center;
            }}
            
            .segment.active .segment-time {{
                background: #667eea;
                color: white;
            }}
            
            .segment-text {{
                flex: 1;
                color: #24292e;
                font-size: 16px;
                line-height: 1.8;
            }}
            
            .segment.active .segment-text {{
                color: #000;
                font-weight: 600;
            }}
            
            @keyframes slideIn {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .segment {{
                animation: slideIn 0.4s ease-out;
            }}
            
            @media (max-width: 768px) {{
                .audio-section {{
                    padding: 15px;
                }}
                
                .controls-section {{
                    flex-direction: column;
                    gap: 15px;
                }}
                
                .transcript-header {{
                    padding: 15px;
                    flex-direction: column;
                    gap: 10px;
                    text-align: center;
                }}
                
                .segment {{
                    margin: 12px 0;
                    padding: 16px 20px;
                }}
                
                .segment-content {{
                    flex-direction: column;
                    gap: 12px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="player-container">
            <div class="audio-section">
                <div class="audio-wrapper">
                    <audio id="audioPlayer" controls>
                        <source src="data:{audio_mime};base64,{audio_base64}" type="{audio_mime}">
                        Seu navegador não suporta o elemento de áudio.
                    </audio>
                </div>
                <div class="progress-bar" id="progressBar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="controls-section">
                    <div class="time-display" id="timeDisplay">00:00 / 00:00</div>
                    <div class="speed-controls">
                        <button class="speed-control" onclick="changeSpeed(0.5)" data-speed="0.5">0.5x</button>
                        <button class="speed-control" onclick="changeSpeed(0.75)" data-speed="0.75">0.75x</button>
                        <button class="speed-control active" onclick="changeSpeed(1)" data-speed="1">1x</button>
                        <button class="speed-control" onclick="changeSpeed(1.25)" data-speed="1.25">1.25x</button>
                        <button class="speed-control" onclick="changeSpeed(1.5)" data-speed="1.5">1.5x</button>
                        <button class="speed-control" onclick="changeSpeed(2)" data-speed="2">2x</button>
                    </div>
                </div>
            </div>
            
            <div class="transcript-section">
                <div class="transcript-header">
                    <div class="transcript-title">🎵 Transcrição Sincronizada</div>
                    <div class="segment-count" id="segmentCount">0 segmentos</div>
                </div>
                <div class="transcript-container" id="transcriptContainer"></div>
            </div>
        </div>
        
        <script>
            const segments = {json.dumps(segments_data)};
            const audio = document.getElementById('audioPlayer');
            const transcriptContainer = document.getElementById('transcriptContainer');
            const timeDisplay = document.getElementById('timeDisplay');
            const progressFill = document.getElementById('progressFill');
            const progressBar = document.getElementById('progressBar');
            const segmentCount = document.getElementById('segmentCount');
            
            segmentCount.textContent = `${{segments.length}} segmentos`;
            
            function formatTime(seconds) {{
                if (isNaN(seconds)) return '00:00';
                const mins = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${{mins.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
            }}
            
            function renderSegments() {{
                transcriptContainer.innerHTML = segments.map((seg, index) => `
                    <div class="segment" 
                         id="${{seg.id}}" 
                         data-start="${{seg.start}}" 
                         data-end="${{seg.end}}"
                         onclick="seekToSegment(${{seg.start}})"
                         style="animation-delay: ${{index * 0.03}}s">
                        <div class="segment-content">
                            <span class="segment-time">${{formatTime(seg.start)}}</span>
                            <span class="segment-text">${{seg.text}}</span>
                        </div>
                    </div>
                `).join('');
            }}
            
            function seekToSegment(time) {{
                audio.currentTime = time;
                if (audio.paused) audio.play();
            }}
            
            function changeSpeed(rate) {{
                audio.playbackRate = rate;
                document.querySelectorAll('.speed-control').forEach(btn => {{
                    btn.classList.toggle('active', parseFloat(btn.dataset.speed) === rate);
                }});
            }}
            
            progressBar.addEventListener('click', (e) => {{
                const rect = progressBar.getBoundingClientRect();
                const percent = (e.clientX - rect.left) / rect.width;
                if (!isNaN(audio.duration)) audio.currentTime = percent * audio.duration;
            }});
            
            let lastActiveSegment = null;
            function updateActiveSegment() {{
                const currentTime = audio.currentTime;
                document.querySelectorAll('.segment').forEach(seg => {{
                    const start = parseFloat(seg.dataset.start);
                    const end = parseFloat(seg.dataset.end);
                    const active = currentTime >= start && currentTime < end;
                    
                    seg.classList.toggle('active', active);
                    seg.classList.toggle('played', currentTime > end);
                    
                    if (active && seg !== lastActiveSegment) {{
                        seg.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        lastActiveSegment = seg;
                    }}
                }});
                
                const duration = audio.duration || 0;
                timeDisplay.textContent = `${{formatTime(currentTime)}} / ${{formatTime(duration)}}`;
                
                if (duration > 0) {{
                    progressFill.style.width = `${{(currentTime / duration) * 100}}%`;
                }}
            }}
            
            audio.addEventListener('timeupdate', updateActiveSegment);
            audio.addEventListener('loadedmetadata', () => {{
                timeDisplay.textContent = `00:00 / ${{formatTime(audio.duration)}}`;
            }});
            
            renderSegments();
        </script>
    </body>
    </html>
    """

    # CORREÇÃO: Remover o parâmetro width="100%" que causava o erro
    # O CSS já controla a largura (width: 100%)
    components.html(html_content, height=height, scrolling=False)


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
