#!/usr/bin/env python3
"""
Script de inicialização da interface web do ClareIA.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

if __name__ == "__main__":
    # Importa e executa o Streamlit
    from streamlit.web import cli as stcli

    # Configura o comando para executar app.web
    sys.argv = [
        "streamlit",
        "run",
        str(root_dir / "app" / "web.py"),
        "--server.port=8501",
        "--server.address=0.0.0.0",
    ]

    # Executa o Streamlit
    sys.exit(stcli.main())
