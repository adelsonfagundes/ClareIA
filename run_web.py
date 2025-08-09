#!/usr/bin/env python3
"""
Script de inicialização da interface web do ClareIA.
Executa diretamente o Streamlit com a aplicação.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Executa o Streamlit com a aplicação web."""
    # Caminho para o arquivo web.py
    web_app = Path(__file__).parent / "app" / "web.py"

    # Comando para executar o Streamlit
    cmd = [
        sys.executable,  # Python atual
        "-m",
        "streamlit",
        "run",
        str(web_app),
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false",
    ]

    print("🚀 Iniciando ClareIA Web Interface...")
    print("📍 Acesse em: http://localhost:8501")
    print("⏹️  Pressione Ctrl+C para parar\n")

    try:
        # Executa o Streamlit como subprocess
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n👋 Encerrando ClareIA...")
        return 0
    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
