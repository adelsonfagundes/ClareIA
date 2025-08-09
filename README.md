# ClareIA — Transcriber & Summarizer (pt-BR)

Ferramenta em Python 3.13 para:
- Transcrever áudios (.mp3/.wav) em português do Brasil usando OpenAI
- Gerar ata, decisões, itens de ação e insights estruturados prontos para uso com modelos da OpenAI

Este README explica passo a passo como instalar, configurar, usar a CLI e inclui um “Cheat Sheet” com os comandos mais comuns.

---

## Requisitos

- Python 3.13
- Chave de API da OpenAI (variável de ambiente `OPENAI_API_KEY`)
- Dependências do projeto (instaladas via `requirements.txt`)

---

## Instalação

1) Crie (ou ative) um ambiente virtual
- Windows (PowerShell):
  ```powershell
  py -m venv .venv
  .\.venv\Scripts\Activate.ps1
  py -m pip install -U pip
  ```
- Linux/Mac (bash/zsh):
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  python -m pip install -U pip
  ```

2) Instale as dependências:
```bash
pip install -r requirements.txt
```

3) Configure suas variáveis (agora com auto-load de .env):
- Opção A — via .env (recomendado para dev):
  - Copie o exemplo:
    - Windows:
      ```powershell
      Copy-Item .env.example .env
      ```
    - Linux/Mac:
      ```bash
      cp .env.example .env
      ```
  - Edite `.env` e defina:
    ```
    OPENAI_API_KEY=sua_chave_aqui
    ```
  - Opcional: crie `.env.local` para overrides locais (sobrescreve valores do `.env`).

- Opção B — via variável de ambiente no shell:
  - Windows (PowerShell):
    ```powershell
    $env:OPENAI_API_KEY="sua_chave_aqui"
    ```
  - Linux/Mac:
    ```bash
    export OPENAI_API_KEY="sua_chave_aqui"
    ```

Observações:
- A aplicação carrega automaticamente `.env` e `.env.local` do diretório atual (ou pais).
- Variáveis já presentes no ambiente do sistema NÃO são sobrescritas por `.env`.
- Se `.env.local` existir, ele pode sobrescrever valores do `.env`.

---

## Visão Geral da CLI

- Executável principal:
  ```bash
  python -m app.cli [--verbose] <comando> [opções]
  ```
- Comandos disponíveis:
  - `transcribe`: transcreve um arquivo de áudio (.mp3/.wav)
  - `summarize`: gera ata/insights a partir de um transcript (.json/.txt) ou diretamente de um áudio (transcreve e resume)

- Flag global:
  - `--verbose`: habilita logs detalhados (útil para depuração)

Ajuda geral:
```bash
python -m app.cli -h
```

---

## 🧾 Cheat Sheet (comandos rápidos)

Dica: paths com espaços devem ser entre aspas. Ex.: "C:\Meus Áudios\reuniao.mp3"

### 1) Setup rápido

- Windows (PowerShell):
  ```powershell
  py -m venv .venv; .\.venv\Scripts\Activate.ps1; py -m pip install -U pip; pip install -r requirements.txt
  Copy-Item .env.example .env; notepad .env  # edite sua chave
  python -m app.cli -h
  ```

- Linux/Mac (bash/zsh):
  ```bash
  python -m venv .venv && source .venv/bin/activate && python -m pip install -U pip && pip install -r requirements.txt
  cp .env.example .env && ${EDITOR:-nano} .env  # edite sua chave
  python -m app.cli -h
  ```

### 2) Transcrever áudio

- JSON detalhado (com segmentos, se disponíveis):
  - Windows:
    ```powershell
    python -m app.cli transcribe .\audios\reuniao.mp3 --format verbose_json -o .\saida\transcript.json --save-json
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli transcribe ./audios/reuniao.mp3 --format verbose_json -o ./saida/transcript.json --save-json
    ```

- Texto simples:
  - Windows:
    ```powershell
    python -m app.cli transcribe .\audios\reuniao.wav -o .\saida\transcript.txt
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli transcribe ./audios/reuniao.wav -o ./saida/transcript.txt
    ```

- Usando Whisper:
  - Windows:
    ```powershell
    python -m app.cli transcribe .\audios\reuniao.mp3 -m whisper-1 -o .\saida\whisper.json --save-json
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli transcribe ./audios/reuniao.mp3 -m whisper-1 -o ./saida/whisper.json --save-json
    ```

- Com dica contextual (melhora nomes/termos):
  - Windows:
    ```powershell
    python -m app.cli transcribe .\audios\reuniao.mp3 `
      --prompt "Participantes: João, Maria; termos: OKR, churn, NPS" `
      --format verbose_json -o .\saida\transcript.json --save-json
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli transcribe ./audios/reuniao.mp3 \
      --prompt "Participantes: João, Maria; termos: OKR, churn, NPS" \
      --format verbose_json -o ./saida/transcript.json --save-json
    ```

- SRT/VTT (exporta legenda; salve sem --save-json):
  - Windows:
    ```powershell
    python -m app.cli transcribe .\audios\reuniao.mp3 --format srt -o .\saida\reuniao.srt
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli transcribe ./audios/reuniao.mp3 --format srt -o ./saida/reuniao.srt
    ```

### 3) Gerar ata/insights

- A partir de transcript JSON existente:
  - Windows:
    ```powershell
    python -m app.cli summarize .\saida\transcript.json -o .\saida\ata.json
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli summarize ./saida/transcript.json -o ./saida/ata.json
    ```

- Diretamente do áudio (transcreve + resume):
  - Windows:
    ```powershell
    python -m app.cli summarize .\audios\reuniao.mp3 -o .\saida\ata.json
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli summarize ./audios/reuniao.mp3 -o ./saida/ata.json
    ```

- Ajustando modelo/temperatura e contexto:
  - Windows:
    ```powershell
    python -m app.cli summarize .\saida\transcript.json `
      -m gpt-4o-mini -t 0.2 `
      -c "Reunião de produto; pauta: Q4; participantes: Ana, Bruno" `
      -o .\saida\ata.json
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli summarize ./saida/transcript.json \
      -m gpt-4o-mini -t 0.2 \
      -c "Reunião de produto; pauta: Q4; participantes: Ana, Bruno" \
      -o ./saida/ata.json
    ```

### 4) Depuração rápida

- Ativar logs detalhados:
  ```bash
  python -m app.cli --verbose transcribe ./audios/reuniao.mp3 -o ./saida/transcript.txt
  ```

- Ajustar timeout e tentativas:
  - Windows:
    ```powershell
    # no .env ou direto no shell
    $env:OPENAI_TIMEOUT="180"; $env:OPENAI_MAX_RETRIES="5"
    ```
  - Linux/Mac:
    ```bash
    export OPENAI_TIMEOUT="180"; export OPENAI_MAX_RETRIES="5"
    ```

- Conferir variável de ambiente:
  - Windows:
    ```powershell
    echo $env:OPENAI_API_KEY
    ```
  - Linux/Mac:
    ```bash
    echo $OPENAI_API_KEY
    ```

---

## Comando: transcribe (detalhado)

Transcreve um arquivo de áudio em pt-BR.

- Forma geral:
  ```bash
  python -m app.cli transcribe <caminho/arquivo.(mp3|wav)> [opções]
  ```

- Argumentos:
  - `input` (posicional): caminho do arquivo `.mp3` ou `.wav`.
  - `-m, --model` (opcional): modelo de transcrição. Padrão: `gpt-4o-transcribe`. Alternativa: `whisper-1`.
  - `-l, --language` (opcional): idioma ISO 639-1. Padrão: `pt`.
  - `-f, --format` (opcional): formato da resposta da API.
    - `text`, `json`, `verbose_json`, `srt`, `vtt` (sugestão: `verbose_json` para segmentos)
  - `--prompt` (opcional): dica contextual (nomes próprios, termos).
  - `-o, --output` (opcional): arquivo de saída (criado).
  - `--save-json` (opcional): salva como JSON do modelo `Transcript`. Sem esta flag, salva texto.

Observações:
- A extensão do arquivo de saída não altera o comportamento; use `--save-json` para JSON.
- Para srt/vtt, use `--format srt|vtt` e não passe `--save-json`.

---

## Comando: summarize (detalhado)

Gera ata/insights estruturados a partir de um transcript (JSON/TXT) ou diretamente do áudio.

- Forma geral:
  ```bash
  python -m app.cli summarize <caminho/(transcript.json|transcript.txt|audio.mp3|audio.wav)> [opções]
  ```

- Argumentos:
  - `input` (posicional): transcript existente ou áudio.
  - `-m, --model` (opcional): modelo para resumo. Padrão: `gpt-4o-mini`.
  - `-t, --temperature` (opcional, float): criatividade. Padrão: `0.2`.
  - `-c, --context` (opcional): contexto adicional (participantes, pauta, objetivos).
  - `-o, --output` (opcional): arquivo `.json` de saída.

Saída: JSON do modelo `MeetingSummary`:
- `title`, `summary`, `key_points`, `decisions`, `action_items`, `insights`

---

## Fluxos comuns

1) Transcrever primeiro e revisar:
```bash
python -m app.cli transcribe ./audios/reuniao.mp3 --format verbose_json -o ./saida/transcript.json --save-json
```
Depois, gerar ata:
```bash
python -m app.cli summarize ./saida/transcript.json -o ./saida/ata.json
```

2) Fazer tudo de uma vez:
```bash
python -m app.cli summarize ./audios/reuniao.mp3 -o ./saida/ata.json
```

---

## Variáveis de ambiente suportadas

- `OPENAI_API_KEY` (obrigatória): chave da API da OpenAI
- `TRANSCRIBE_MODEL` (opcional): padrão `gpt-4o-transcribe`
- `TRANSCRIBE_LANGUAGE` (opcional): padrão `pt`
- `TRANSCRIBE_FORMAT` (opcional): padrão `json`
- `SUMMARY_MODEL` (opcional): padrão `gpt-4o-mini`
- `SUMMARY_TEMPERATURE` (opcional): padrão `0.2`
- `OPENAI_TIMEOUT` (opcional): padrão `120` (segundos)
- `OPENAI_MAX_RETRIES` (opcional): padrão `3`

Dicas:
- `.env` é carregado automaticamente; `.env.local` pode sobrescrever chaves do `.env`.
- Variáveis já definidas no ambiente do sistema têm precedência sobre arquivos.

---

## Logs e depuração

- Adicione `--verbose` ao comando para logs detalhados.
- Mensagens comuns:
  - Falta de variável: `OPENAI_API_KEY não encontrado`
  - Arquivo não encontrado: caminho incorreto
  - Formato não suportado: use `.mp3` ou `.wav`
  - Timeout: aumente `OPENAI_TIMEOUT`

---

## Códigos de saída (exit codes)

- `0`: sucesso
- `1`: falha em tempo de execução (ex.: erro da API, arquivo inválido)
- `2`: variável `OPENAI_API_KEY` ausente

---

## Solução de problemas (Troubleshooting)

- ImportError ao iniciar:
  - Garanta que existe o arquivo `app/__init__.py` (com dois underscores em cada lado).
- “Formato de arquivo não suportado”:
  - Aceitos: `.mp3` e `.wav`. Verifique a extensão.
- “401/403” da API:
  - Verifique a chave de API e o projeto correto na OpenAI.
- “Timeout” ou “network error”:
  - Aumente `OPENAI_TIMEOUT`, verifique conexão, tente novamente.
- Salvei `.json` sem `--save-json`:
  - O formato salvo depende da flag `--save-json` (não da extensão). Use `--save-json` para JSON.

---

## Roadmap (próximos passos sugeridos)

- API REST (FastAPI) com upload
- Diarização e identificação de falantes
- Exportações SRT/VTT melhoradas e marcação por tópicos
- Histórico (SQLite/Postgres)
- Testes automatizados e qualidade (ruff/black/mypy)

---

## Licença

MIT
