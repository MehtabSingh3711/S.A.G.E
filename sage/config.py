"""SAGE configuration — all settings, paths, and model config."""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# ── GLM-5 via Ollama ─────────────────────────────────────────────
OLLAMA_MODEL = "deepseek-v3.1:671b-cloud"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ── Obsidian vault path ──────────────────────────────────────────
VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./sage_vault"))

# ── NotebookLM ───────────────────────────────────────────────────
NOTEBOOKLM_NOTEBOOK_ID = os.getenv("NOTEBOOKLM_NOTEBOOK_ID")

# ── Pipeline settings ────────────────────────────────────────────
MAX_RETRIEVAL_DEPTH = 2        # max follow-up queries per cluster
MIN_ANSWER_LENGTH = 500        # chars — below this triggers follow-up
TOPICS_PER_CLUSTER = 3         # max topics grouped into one cluster
