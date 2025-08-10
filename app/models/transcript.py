from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class TranscriptSegment(BaseModel):
    start: float | None = Field(default=None, description="Início do segmento em segundos")
    end: float | None = Field(default=None, description="Fim do segmento em segundos")
    text: str = Field(description="Texto do segmento")
    speaker: str | None = Field(default=None, description="Possível falante, se disponível")

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_timestamps(cls, v):
        """Valida e converte timestamps para float."""
        if v is None:
            return None

        try:
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                cleaned = v.strip()
                if cleaned == "" or cleaned.lower() in ("none", "null", "nan"):
                    return None
                return float(cleaned)
            return None
        except (ValueError, TypeError):
            return None


class Transcript(BaseModel):
    text: str = Field(description="Transcrição completa em texto")
    language: str = Field(default="pt", description="Idioma detectado/forçado")
    segments: list[TranscriptSegment] | None = Field(
        default=None, description="Segmentos com timestamps (se disponíveis)"
    )
    source_path: str | None = Field(default=None, description="Caminho do arquivo de origem")

    @staticmethod
    def from_verbose_json(data: dict, fallback_language: str = "pt", source_path: str | None = None) -> Transcript:
        """Cria Transcript a partir de verbose_json com validação robusta."""
        try:
            text = data.get("text") or ""
            lang = data.get("language") or fallback_language
            raw_segments = data.get("segments") or []

            segments = []
            for i, s in enumerate(raw_segments):
                try:
                    # Validar e converter timestamps
                    start_time = s.get("start")
                    end_time = s.get("end")
                    segment_text = s.get("text") or ""

                    # Criar segmento com validação
                    segment = TranscriptSegment(
                        start=start_time,
                        end=end_time,
                        text=segment_text,
                    )
                    segments.append(segment)

                except Exception as e:
                    # Log do erro mas continua processando outros segmentos
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(f"Erro ao processar segmento {i}: {e}")

                    # Criar segmento básico como fallback
                    segment = TranscriptSegment(
                        start=None,
                        end=None,
                        text=s.get("text", ""),
                    )
                    segments.append(segment)

            return Transcript(text=text, language=lang, segments=segments or None, source_path=source_path)

        except Exception:
            import logging

            logger = logging.getLogger(__name__)
            logger.exception("Erro ao processar verbose_json")

            # Fallback: criar transcript básico
            return Transcript(
                text=data.get("text", "Erro no processamento"),
                language=fallback_language,
                segments=None,
                source_path=source_path,
            )
