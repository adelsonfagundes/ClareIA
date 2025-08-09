# ClareIA — Transcriber & Summarizer (pt-BR)

Ferramenta moderna em Python 3.13 para transcrição inteligente e análise de reuniões:
- 🎙️ **Transcrição precisa** de áudios (.mp3/.wav/.m4a) em português do Brasil usando OpenAI
- 📊 **Geração automática** de atas estruturadas com decisões, itens de ação e insights
- 🖥️ **Interface Web intuitiva** com Streamlit para uso simplificado
- 🤖 **Suporte completo** aos modelos mais recentes da OpenAI (gpt-4o-transcribe e whisper-1)

---

## 🚀 Novidades

### v0.1.0
- ✨ **Interface Web com Streamlit** - Use o ClareIA sem comandos, direto no navegador!
- 🎯 **Código 100% limpo** - Validado com Ruff seguindo as melhores práticas Python
- 📦 **Arquitetura modular** - Organização clara com models, services e core
- 🔄 **Suporte a múltiplos formatos** - JSON, SRT, VTT para transcrições
- 📄 **Export em Markdown** - Baixe atas formatadas prontas para compartilhar

---

## 📋 Requisitos

- Python 3.13+
- Chave de API da OpenAI (variável `OPENAI_API_KEY`)
- 8GB RAM recomendado para processar áudios longos

---

## 🔧 Instalação

### 1️⃣ Clone o repositório
```bash
git clone https://github.com/adelsonfagundes/ClareIA.git
cd ClareIA
```

### 2️⃣ Crie e ative o ambiente virtual

**Windows (PowerShell):**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -U pip
```

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

### 3️⃣ Instale as dependências
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure a API Key

**Opção A - Arquivo .env (Recomendado):**
```bash
# Windows
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

Edite o arquivo `.env`:
```env
OPENAI_API_KEY=sk-sua-chave-aqui
```

**Opção B - Variável de ambiente:**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-sua-chave-aqui"

# Linux/Mac
export OPENAI_API_KEY="sk-sua-chave-aqui"
```

---

## 🌐 Interface Web (Novo!)

### Iniciando a interface

```bash
# Método recomendado
python run_web.py

# Método alternativo
streamlit run app/web.py
```

Acesse: http://localhost:8501

### Recursos da Interface Web

- 📤 **Upload simples** - Arraste ou selecione arquivos de áudio
- ⚙️ **Configurações visuais** - Ajuste modelos e parâmetros facilmente
- 📊 **Visualização rica** - Veja transcrições e atas formatadas
- 💾 **Downloads múltiplos** - Exporte em JSON ou Markdown
- 📈 **Estatísticas em tempo real** - Acompanhe métricas do processamento

### Screenshots

<details>
<summary>Ver interface</summary>

- **Tela principal**: Upload e configurações lado a lado
- **Transcrição**: Texto editável com métricas
- **Ata gerada**: Decisões e ações organizadas visualmente
- **Export**: Botões para JSON e Markdown

</details>

---

## 💻 Interface CLI

### Comandos Principais

#### Transcrever áudio
```bash
# Transcrição básica
python -m app.cli transcribe "audio.mp3" -o transcript.json --save-json

# Com dicas contextuais para melhor precisão
python -m app.cli transcribe "reuniao.m4a" \
  --prompt "Participantes: João, Maria; Termos: OKR, NPS" \
  --format json -o transcript.json --save-json

# Com timestamps (requer whisper-1)
python -m app.cli transcribe "audio.wav" \
  -m whisper-1 --format verbose_json \
  -o transcript_timestamps.json --save-json
```

#### Gerar ata/resumo
```bash
# A partir de transcrição existente
python -m app.cli summarize transcript.json -o ata.json

# Direto do áudio (transcreve + resume)
python -m app.cli summarize "reuniao.mp3" -o ata.json

# Com contexto adicional
python -m app.cli summarize transcript.json \
  -m gpt-4o-mini -t 0.2 \
  -c "Reunião Q4, participantes: time de produto" \
  -o ata_detalhada.json
```

### Opções Avançadas

```bash
# Ativar logs detalhados
python -m app.cli --verbose transcribe "audio.mp3"

# Ajustar timeout para arquivos grandes
export OPENAI_TIMEOUT=300  # 5 minutos
export OPENAI_MAX_RETRIES=5
```

---

## 🤖 Modelos Suportados

### Transcrição

| Modelo | Formatos | Características |
|--------|----------|----------------|
| **gpt-4o-transcribe** | `json`, `text` | Mais recente e preciso, otimizado para português |
| **whisper-1** | `json`, `text`, `verbose_json`, `srt`, `vtt` | Suporta timestamps e legendas |

### Sumarização

| Modelo | Uso Recomendado |
|--------|-----------------|
| **gpt-4o-mini** | Rápido e eficiente, ideal para atas |
| **gpt-4o** | Máxima capacidade, análises complexas |
| **gpt-3.5-turbo** | Alternativa econômica |

---

## 📁 Estrutura do Projeto

```
ClareIA/
├── app/
│   ├── core/           # Lógica principal
│   │   ├── config.py   # Configurações e env vars
│   │   ├── transcriber.py  # Motor de transcrição
│   │   └── summarizer.py   # Gerador de atas
│   ├── models/         # Modelos Pydantic
│   │   ├── transcript.py   # Estrutura da transcrição
│   │   └── summary.py      # Estrutura da ata
│   ├── services/       # Integrações
│   │   └── openai_client.py
│   ├── cli.py          # Interface de linha de comando
│   └── web.py          # Interface Streamlit
├── .streamlit/         # Configurações Streamlit
├── run_web.py          # Launcher da interface web
├── requirements.txt    # Dependências
└── pyproject.toml      # Configurações Ruff
```

---

## ⚙️ Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OPENAI_API_KEY` | - | **Obrigatória** - Sua chave da API |
| `TRANSCRIBE_MODEL` | `gpt-4o-transcribe` | Modelo de transcrição |
| `TRANSCRIBE_LANGUAGE` | `pt` | Idioma padrão |
| `TRANSCRIBE_FORMAT` | `json` | Formato de saída |
| `SUMMARY_MODEL` | `gpt-4o-mini` | Modelo para resumos |
| `SUMMARY_TEMPERATURE` | `0.2` | Criatividade (0.0-1.0) |
| `OPENAI_TIMEOUT` | `120` | Timeout em segundos |
| `OPENAI_MAX_RETRIES` | `3` | Tentativas em caso de erro |

---

## 🧪 Qualidade de Código

O projeto segue rigorosos padrões de qualidade:

```bash
# Verificar código com Ruff
ruff check .

# Formatar código
ruff format .

# Configuração em pyproject.toml
# - 120 caracteres por linha
# - Type hints obrigatórios
# - Docstrings em formato Google
# - Imports organizados
```

---

## 📊 Exemplos de Uso

### Caso 1: Reunião de Produto
```python
# Transcrever com contexto
python -m app.cli transcribe "reuniao_produto.mp3" \
  --prompt "Produto: App Mobile, Métricas: DAU, MAU, Churn" \
  -o transcript.json --save-json

# Gerar ata detalhada
python -m app.cli summarize transcript.json \
  -c "Sprint Planning Q1 2025" \
  -o ata_produto.json
```

### Caso 2: Entrevista
```python
# Usar whisper para timestamps
python -m app.cli transcribe "entrevista.m4a" \
  -m whisper-1 --format verbose_json \
  -o entrevista_timestamps.json --save-json
```

---

## 🚧 Roadmap

- [x] Interface web com Streamlit
- [x] Código 100% validado com Ruff
- [x] Export em Markdown
- [ ] Suporte a upload múltiplo
- [ ] Diarização (identificação de falantes)
- [ ] API REST com FastAPI
- [ ] Histórico em banco de dados
- [ ] Integração com Google Drive/Dropbox
- [ ] Dashboard de analytics
- [ ] Testes automatizados com pytest

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Valide com Ruff (`ruff check . --fix`)
4. Commit (`git commit -m 'feat: adiciona MinhaFeature'`)
5. Push (`git push origin feature/MinhaFeature`)
6. Abra um Pull Request

---

## 📝 Licença

MIT - veja [LICENSE](LICENSE) para detalhes.

---

## 👨‍💻 Autor

**Adelson Fagundes**
- GitHub: [@adelsonfagundes](https://github.com/adelsonfagundes)

---

## 🙏 Agradecimentos

- OpenAI pela API de transcrição e modelos
- Streamlit pela framework de interface
- Comunidade Python pelas ferramentas incríveis

---

<div align="center">
  
**⭐ Se este projeto te ajudou, considere dar uma estrela!**

[Reportar Bug](https://github.com/adelsonfagundes/ClareIA/issues) · 
[Sugerir Feature](https://github.com/adelsonfagundes/ClareIA/issues)

</div>