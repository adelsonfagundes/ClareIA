from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    start: Optional[float] = Field(default=None, description="Início do segmento em segundos")
    end: Optional[float] = Field(default=None, description="Fim do segmento em segundos")
    text: str = Field(description="Texto do segmento")
    speaker: Optional[str] = Field(default=None, description="Possível falante, se disponível")


class Transcript(BaseModel):
    text: str = Field(description="Transcrição completa em texto")
    language: str = Field(default="pt", description="Idioma detectado/forçado")
    segments: Optional[List[TranscriptSegment]] = Field(
        default=None, description="Segmentos com timestamps (se disponíveis)"
    )
    source_path: Optional[str] = Field(default=None, description="Caminho do arquivo de origem")

    @staticmethod
    def from_verbose_json(data: dict, fallback_language: str = "pt", source_path: Optional[str] = None) -> "Transcript":
        text = data.get("text") or ""
        lang = data.get("language") or fallback_language
        raw_segments = data.get("segments") or []
        segments = []
        for s in raw_segments:
            segments.append(
                TranscriptSegment(
                    start=s.get("start"),
                    end=s.get("end"),
                    text=s.get("text") or "",
                )
            )
        return Transcript(text=text, language=lang, segments=segments or None, source_path=source_path)
