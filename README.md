# ClareIA — Transcriber & Summarizer (pt-BR)

Ferramenta em Python 3.13 para:
- Transcrever áudios (.mp3/.wav/.m4a) em português do Brasil usando OpenAI
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

3) Configure suas variáveis (auto-load de .env habilitado):
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

## Compatibilidade de formatos por modelo

- gpt-4o-transcribe: suporta apenas `response_format = json` ou `text`.
- whisper-1: suporta `text`, `json`, `verbose_json`, `srt`, `vtt` (inclui segments/timestamps).

Se você precisa de segments/timestamps, use `-m whisper-1` com `--format verbose_json` (ou `srt`/`vtt`).

---

## Visão Geral da CLI

- Executável principal:
  ```bash
  python -m app.cli [--verbose] <comando> [opções]
  ```
- Comandos disponíveis:
  - `transcribe`: transcreve um arquivo de áudio (.mp3/.wav/.m4a)
  - `summarize`: gera ata/insights a partir de um transcript (.json/.txt) ou diretamente de um áudio (transcreve e resume)

- Flag global:
  - `--verbose`: habilita logs detalhados (útil para depuração)

Ajuda geral:
```bash
python -m app.cli -h
```

---

## 🧾 Cheat Sheet (comandos rápidos)

Dica: paths com espaços devem ser entre aspas. Ex.: "C:\Meus Áudios\reuniao.m4a"

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

- JSON simples (gpt-4o-transcribe):
  - Windows:
    ```powershell
    python -m app.cli transcribe ".\audios\reuniao.m4a" --format json -o .\saida\transcript.json --save-json
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli transcribe "./audios/reuniao.m4a" --format json -o ./saida/transcript.json --save-json
    ```

- Segments/timestamps (verbose_json com Whisper):
  - Windows:
    ```powershell
    python -m app.cli transcribe ".\audios\reuniao.m4a" -m whisper-1 --format verbose_json -o .\saida\transcript.json --save-json
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli transcribe "./audios/reuniao.m4a" -m whisper-1 --format verbose_json -o ./saida/transcript.json --save-json
    ```

- SRT/VTT (com Whisper):
  - Windows:
    ```powershell
    python -m app.cli transcribe ".\audios\reuniao.m4a" -m whisper-1 --format srt -o .\saida\reuniao.srt
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli transcribe "./audios/reuniao.m4a" -m whisper-1 --format srt -o ./saida/reuniao.srt
    ```

- Com dica contextual (melhora nomes/termos):
  - Windows:
    ```powershell
    python -m app.cli transcribe ".\audios\reuniao.m4a" `
      --prompt "Participantes: João, Maria; termos: OKR, churn, NPS" `
      --format json -o .\saida\transcript.json --save-json
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli transcribe "./audios/reuniao.m4a" \
      --prompt "Participantes: João, Maria; termos: OKR, churn, NPS" \
      --format json -o ./saida/transcript.json --save-json
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
    python -m app.cli summarize ".\audios\reuniao.m4a" -o .\saida\ata.json
    ```
  - Linux/Mac:
    ```bash
    python -m app.cli summarize "./audios/reuniao.m4a" -o ./saida/ata.json
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
  python -m app.cli --verbose transcribe "./audios/reuniao.m4a" --format json -o ./saida/transcript.json --save-json
  ```

- Ajustar timeout e tentativas:
  - Windows:
    ```powershell
    $env:OPENAI_TIMEOUT="180"; $env:OPENAI_MAX_RETRIES="5"
    ```
  - Linux/Mac:
    ```bash
    export OPENAI_TIMEOUT="180"; export OPENAI_MAX_RETRIES="5"
    ```

---

## Comando: transcribe (detalhado)

Transcreve um arquivo de áudio em pt-BR.

- Forma geral:
  ```bash
  python -m app.cli transcribe <caminho/arquivo.(mp3|wav|m4a)> [opções]
  ```

- Argumentos:
  - `input` (posicional): caminho do arquivo `.mp3`, `.wav` ou `.m4a`.
  - `-m, --model` (opcional): modelo de transcrição. Padrão: `gpt-4o-transcribe`. Alternativa: `whisper-1`.
  - `-l, --language` (opcional): idioma ISO 639-1. Padrão: `pt`.
  - `-f, --format` (opcional): formato da resposta da API.
    - Para `gpt-4o-transcribe`: `text` ou `json`
    - Para `whisper-1`: `text`, `json`, `verbose_json`, `srt`, `vtt`
  - `--prompt` (opcional): dica contextual (nomes próprios, termos).
  - `-o, --output` (opcional): arquivo de saída (criado).
  - `--save-json` (opcional): salva como JSON do modelo `Transcript`. Sem esta flag, salva texto.

Observações:
- A extensão do arquivo de saída não altera o comportamento; use `--save-json` para JSON.
- Para srt/vtt/verbose_json você deve usar `-m whisper-1`.

---

## Comando: summarize (detalhado)

Gera ata/insights estruturados a partir de um transcript (JSON/TXT) ou diretamente do áudio.

- Forma geral:
  ```bash
  python -m app.cli summarize <caminho/(transcript.json|transcript.txt|audio.mp3|audio.wav|audio.m4a)> [opções]
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

## Variáveis de ambiente suportadas

- `OPENAI_API_KEY` (obrigatória): chave da API da OpenAI
- `TRANSCRIBE_MODEL` (opcional): padrão `gpt-4o-transcribe`
- `TRANSCRIBE_LANGUAGE` (opcional): padrão `pt`
- `TRANSCRIBE_FORMAT` (opcional): padrão `json`
- `SUMMARY_MODEL` (opcional): padrão `gpt-4o-mini`
- `SUMMARY_TEMPERATURE` (opcional): padrão `0.2`
- `OPENAI_TIMEOUT` (opcional): padrão `120` (segundos)
- `OPENAI_MAX_RETRIES` (opcional): padrão `3`

---

## Logs e depuração

- Adicione `--verbose` ao comando para logs detalhados.
- Mensagens comuns:
  - Falta de variável: `OPENAI_API_KEY não encontrado`
  - Arquivo não encontrado: caminho incorreto
  - Formato não suportado:
    - Use `.mp3`, `.wav` ou `.m4a`
    - Lembre: `verbose_json/srt/vtt` exigem `-m whisper-1`
  - Timeout: aumente `OPENAI_TIMEOUT`

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