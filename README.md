<p align="center">
  <img src="https://github.com/user-attachments/assets/ea0d715a-031e-4775-88c4-ff836f484174" alt="SAGE Banner" width="800">
</p>

<h1 align="center">🦉 SAGE</h1>
<p align="center">
  <strong>Study · Ask · Generate · Explain</strong>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.11+-green.svg" alt="Python 3.11+"></a>
  <a href="https://ollama.com"><img src="https://img.shields.io/badge/LLM-Ollama-blueviolet.svg" alt="Ollama"></a>
  <a href="https://obsidian.md"><img src="https://img.shields.io/badge/Export-Obsidian-7C3AED.svg" alt="Obsidian"></a>
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-demo">Demo</a> •
  <a href="#-features">Features</a> •
  <a href="#%EF%B8%8F-architecture">Architecture</a> •
  <a href="#-quickstart">Quickstart</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-roadmap">Roadmap</a> •
  <a href="#-license">License</a>
</p>

---

## ✨ Overview

**SAGE** is an AI-powered study agent that transforms a list of topics or a syllabus into comprehensive, production-quality Markdown notes — ready for [Obsidian](https://obsidian.md).

It combines the **grounded retrieval** of [NotebookLM](https://notebooklm.google.com) with the **planning intelligence** of local LLMs via [Ollama](https://ollama.com), orchestrated through a [LangGraph](https://github.com/langchain-ai/langgraph) multi-agent pipeline.

> **Why SAGE?**  
> Unlike generic AI note-takers, SAGE *understands context*. It clusters related topics, evaluates retrieval depth, and performs autonomous follow-up research to ensure every note is comprehensive and accurate — without hallucination.

---

## 🎬 Demo

<video src="https://github.com/user-attachments/assets/9aa1934d-4845-43ec-a9f6-58d00fdbee7e" width = 1080 height = 720 controls>Demo Video</video>

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🧠 **Intelligent Clustering** | Groups fragmented topics into logical clusters for better narrative flow |
| 📚 **Grounded Retrieval** | Uses your own sources (PDFs, URLs, Transcripts) via NotebookLM — zero hallucination |
| 🔄 **Autonomous Loop** | Self-evaluates answers and triggers follow-up retrievals when data is insufficient |
| ✍️ **Synthesis Engine** | Generates beautiful Markdown with Mermaid diagrams, tables, and structured hierarchy |
| 🎨 **AI Studio Integration** | Automatically creates infographics and visual artifacts for your notes |
| 🏢 **Obsidian Vault Sync** | Direct export preserving your subject hierarchy and folder structure |
| 💻 **Interactive CLI** | Premium terminal experience with live progress bars, spinners, and rich panels |

---

## 🏗️ Architecture

SAGE is built on a **LangGraph** multi-agent pipeline. Six specialized nodes handle distinct stages of the study process:

<p align="center">
  <img src="https://github.com/user-attachments/assets/e16c219f-ff84-406b-92fc-53cf9864570b" alt="SAGE Workflow" width="800">
</p>

### Node Breakdown

| Node | Role | Engine |
|---|---|---|
| **Planner** | Analyzes the subject and creates a logical *Study Roadmap* by clustering topics | Ollama (GLM-5) |
| **Retriever** | Searches your configured NotebookLM sources for specific technical details | NotebookLM MCP |
| **Evaluator** | Checks if retrieved content covers the requested syllabus points sufficiently | Rules-based |
| **Writer** | Synthesizes retrieved data into structured Markdown with diagrams and hierarchy | Ollama (GLM-5) |
| **Studio** | Generates infographics and visual artifacts to complement study materials | AI Studio |
| **Publisher** | Builds final Markdown files with frontmatter and saves to your Obsidian vault | File I/O |

---

## ⚡ Quickstart

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.11+ | [Download](https://www.python.org/downloads/) |
| **Ollama** | Latest | [Install](https://ollama.com/download) |
| **NotebookLM CLI** | 0.3.0+ | `pip install notebooklm-py[browser]` |
| **Obsidian** | Any | [Download](https://obsidian.md) *(optional, for viewing notes)* |

### 1. Clone the Repository

```bash
git clone https://github.com/MehtabSingh3711/SAGE.git
cd SAGE
```

### 2. Set Up a Virtual Environment

```bash
# Create
python -m venv .venv

# Activate
# Linux / macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -e ./sage
```

Or install directly from `pyproject.toml`:

```bash
cd sage
pip install -r pyproject.toml
```

### 4. Pull the LLM Model

```bash
ollama pull deepseek-v3.1:671b-cloud
```

### 5. Authenticate with NotebookLM

```bash
notebooklm login
```

### 6. Configure Environment

```bash
# Copy the example config
cp .env.example sage/.env

# Edit with your values
# Linux / macOS:
nano sage/.env
# Windows:
notepad sage/.env
```

### 7. Run the Setup Wizard

```bash
python sage/main.py init
```

This interactive wizard will verify your Ollama connection, NotebookLM authentication, and vault path.

---

## 📖 Usage

### Start a Study Session

```bash
python sage/main.py study --unit "Unit 1 — Introduction to NLP" --subject "NLP"
```

### Load Topics from a File

```bash
python sage/main.py study \
  --unit "Unit 2" \
  --subject "System Design" \
  --syllabus sage/SDunit2.txt
```

### Pass Topics Directly

```bash
python sage/main.py study \
  --unit "Unit 1" \
  --subject "NLP" \
  --topics "Tokenization, Word Embeddings, Attention Mechanism"
```

### Preview the Plan (Dry Run)

```bash
python sage/main.py study --unit "Unit 1" --subject "NLP" --dry-run
```

### Check Status

```bash
python sage/main.py status
```

### CLI Reference

| Command | Flag | Description |
|---|---|---|
| `study` | `-u`, `--unit` | Unit name (e.g. `"Unit 1"`) |
| | `-s`, `--subject` | Subject name (e.g. `"NLP"`) |
| | `-t`, `--topics` | Comma-separated topic list |
| | `--syllabus` | Path to `.txt` file with topics |
| | `-n`, `--unit-number` | Unit number for PDF parsing |
| | `--dry-run` | Show plan without executing |
| | `--resume` | Resume from last checkpoint |
| `status` | — | Show notebook + vault stats |
| `init` | — | First-time setup wizard |

---

## ⚙️ Configuration

All configuration is managed via `sage/.env`. See [`.env.example`](.env.example) for all available options:

```env
# Ollama base URL (default: http://localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434

# NotebookLM Notebook ID (from your NotebookLM URL)
NOTEBOOKLM_NOTEBOOK_ID=your_notebook_id_here
# You can get this by running the command in your terminal
## ------- notebooklm list -------

# Obsidian vault path (absolute path recommended)
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
```

### Pipeline Tuning

These constants in `sage/config.py` control pipeline behavior:

| Setting | Default | Description |
|---|---|---|
| `MAX_RETRIEVAL_DEPTH` | `2` | Max follow-up queries per cluster |
| `MIN_ANSWER_LENGTH` | `500` | Char threshold — below this triggers follow-up |
| `TOPICS_PER_CLUSTER` | `3` | Max topics grouped into one cluster |

---

## 📁 Project Structure

```
SAGE/
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
├── LICENSE               # MIT License
├── README.md             # You are here
│
├── sage/                 # Core application
│   ├── .env              # Your local config (git-ignored)
│   ├── main.py           # CLI entry point (Typer)
│   ├── config.py         # Settings & model config
│   ├── pyproject.toml    # Dependencies
│   │
│   ├── core/             # Pipeline engine
│   │   ├── pipeline.py   # LangGraph pipeline definition
│   │   ├── state.py      # SAGEState schema
│   │   ├── chat.py       # Interactive chat mode
│   │   └── nodes/        # Pipeline nodes
│   │       ├── planner.py
│   │       ├── retriever.py
│   │       ├── evaluator.py
│   │       ├── writer.py
│   │       ├── studio.py
│   │       └── publisher.py
│   │
│   ├── prompts/          # LLM prompt templates
│   ├── ui/               # Rich terminal UI components
│   └── diagrams/         # UML / architecture diagrams
│
├── books/                # Reference materials
└── docs/
    └── RECORDING_GUIDE.md  # How to record a demo video
```

---

## 🗺️ Roadmap

- [ ] PDF syllabus parsing (auto-extract topics from scanned syllabi)
- [ ] Multi-notebook support (pull from multiple NotebookLM notebooks)
- [ ] Resume & checkpoint system (pick up where you left off)
- [ ] Web UI dashboard (monitor pipeline in the browser)
- [ ] Spaced-repetition flashcard generation
- [ ] Export to Anki / Quizlet

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/MehtabSingh3711">Mehtab Singh</a>
</p>
