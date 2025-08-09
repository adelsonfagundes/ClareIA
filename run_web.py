#!/usr/bin/env python3
"""Script de inicialização da interface web do ClareIA."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Executa o Streamlit com a aplicação web."""
    web_app = Path(__file__).parent / "app" / "web.py"

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(web_app),
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false",
    ]

    try:
        result = subprocess.run(cmd, check=True)  # noqa: S603
    except subprocess.CalledProcessError as e:
        return e.returncode
    except KeyboardInterrupt:
        return 0
    except Exception:
        return 1
    else:
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())
