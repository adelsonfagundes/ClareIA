from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

from colorama import Fore, Style, init as colorama_init

from app import __version__ as APP_VERSION
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.summarizer import summarize_transcript
from app.core.transcriber import save_transcript, transcribe_file
from app.models.transcript import Transcript

# Inicializa colorama para Windows e TTYs
colorama_init(autoreset=True)


def _print_header():
    print(f"{Fore.CYAN}Transcriber & Summarizer CLI{Style.RESET_ALL} v{APP_VERSION}")


def cmd_transcribe(args: argparse.Namespace) -> int:
    settings = get_settings()
    model = args.model or settings.default_transcribe_model
    language = args.language or settings.default_language
    response_format = args.format or settings.default_response_format

    transcript = transcribe_file(
        args.input,
        model=model,
        language=language,
        response_format=response_format,  # 'json' ou 'verbose_json' (se whisper-1)
        prompt=args.prompt,
    )

    if args.output:
        out_fmt = "json" if args.save_json else "txt"
        save_transcript(transcript, args.output, as_format=out_fmt)
    else:
        # Se não informaram saída, imprime preview no stdout
        print(f"{Fore.GREEN}Transcrição:{Style.RESET_ALL}\n")
        print(transcript.text[:4000] + ("..." if len(transcript.text) > 4000 else ""))

    return 0


def _load_transcript_from_path(path: str) -> Transcript:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    ext = os.path.splitext(path)[1].lower()
    if ext in {".json"}:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Transcript.model_validate(data)
    elif ext in {".txt"}:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return Transcript(text=text, language="pt", segments=None, source_path=path)
    else:
        # Se for áudio (.mp3/.wav/.m4a), vamos transcrever primeiro
        return transcribe_file(path)


def cmd_summarize(args: argparse.Namespace) -> int:
    settings = get_settings()

    # Se input for áudio, transcreve antes
    transcript = _load_transcript_from_path(args.input)

    summary = summarize_transcript(
        transcript,
        model=args.model or settings.summary_model,
        temperature=args.temperature,
        extra_context=args.context,
    )

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(summary.model_dump(), f, ensure_ascii=False, indent=2)
        print(f"{Fore.GREEN}Ata/insights salvos em{Style.RESET_ALL} {args.output}")
    else:
        print(f"{Fore.MAGENTA}Ata/Insights:{Style.RESET_ALL}\n")
        print(json.dumps(summary.model_dump(), ensure_ascii=False, indent=2))

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app",
        description=(
            "Ferramenta para transcrever áudios e gerar ata/insights com OpenAI.\n\n"
            "Compatibilidade de formatos:\n"
            "- gpt-4o-transcribe: suporta apenas response_format = json ou text\n"
            "- whisper-1: suporta json, text, verbose_json, srt, vtt"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--verbose", action="store_true", help="Ativa logs em nível DEBUG")

    sub = parser.add_subparsers(dest="command", required=True)

    # Subcomando: transcribe
    p_tr = sub.add_parser("transcribe", help="Transcreve um arquivo de áudio (mp3/wav/m4a)")
    p_tr.add_argument("input", help="Caminho para o arquivo .mp3, .wav ou .m4a")
    p_tr.add_argument(
        "-m",
        "--model",
        default=None,
        help="Modelo de transcrição (ex: gpt-4o-transcribe, whisper-1)",
    )
    p_tr.add_argument("-l", "--language", default=None, help="Idioma (ex: pt)")
    p_tr.add_argument(
        "-f",
        "--format",
        default=None,
        choices=["text", "json", "verbose_json", "srt", "vtt"],
        help=(
            "Formato de saída da API de transcrição.\n"
            "- gpt-4o-transcribe: use 'json' ou 'text'\n"
            "- whisper-1: permite 'verbose_json'/'srt'/'vtt' (além de 'json'/'text')"
        ),
    )
    p_tr.add_argument(
        "--prompt",
        default=None,
        help="Dica contextual (nomes próprios, termos técnicos)",
    )
    p_tr.add_argument(
        "-o",
        "--output",
        default=None,
        help="Arquivo para salvar a transcrição (json ou txt)",
    )
    p_tr.add_argument(
        "--save-json",
        action="store_true",
        help="Força salvar a transcrição como JSON (default é txt se format=text)",
    )
    p_tr.set_defaults(func=cmd_transcribe)

    # Subcomando: summarize
    p_sm = sub.add_parser(
        "summarize",
        help="Gera ata/insights a partir de um transcript (json/txt) ou de um áudio (.mp3/.wav/.m4a, transcreve e resume).",
    )
    p_sm.add_argument(
        "input",
        help="Caminho do transcript (.json/.txt) ou do arquivo de áudio (.mp3/.wav/.m4a)",
    )
    p_sm.add_argument("-m", "--model", default=None, help="Modelo para resumo (ex: gpt-4o-mini)")
    p_sm.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=None,
        help="Temperatura do modelo (0.0 a 1.0)",
    )
    p_sm.add_argument(
        "-c",
        "--context",
        default=None,
        help="Contexto adicional (ex: participantes, objetivo da reunião)",
    )
    p_sm.add_argument(
        "-o",
        "--output",
        default=None,
        help="Arquivo de saída (.json) para a ata/insights",
    )
    p_sm.set_defaults(func=cmd_summarize)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging(verbose=args.verbose)
    _print_header()

    if not os.getenv("OPENAI_API_KEY"):
        print(
            f"{Fore.RED}Erro:{Style.RESET_ALL} OPENAI_API_KEY não encontrado. "
            "Defina a variável de ambiente ou preencha o .env (se utilizar)."
        )
        return 2

    try:
        return args.func(args)  # type: ignore[attr-defined]
    except Exception as e:
        print(f"{Fore.RED}Falha:{Style.RESET_ALL} {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
