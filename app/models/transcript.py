from __future__ import annotations

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    start: float | None = Field(default=None, description="Início do segmento em segundos")
    end: float | None = Field(default=None, description="Fim do segmento em segundos")
    text: str = Field(description="Texto do segmento")
    speaker: str | None = Field(default=None, description="Possível falante, se disponível")


class Transcript(BaseModel):
    text: str = Field(description="Transcrição completa em texto")
    language: str = Field(default="pt", description="Idioma detectado/forçado")
    segments: list[TranscriptSegment] | None = Field(
        default=None, description="Segmentos com timestamps (se disponíveis)"
    )
    source_path: str | None = Field(default=None, description="Caminho do arquivo de origem")

    @staticmethod
    def from_verbose_json(data: dict, fallback_language: str = "pt", source_path: str | None = None) -> Transcript:
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
