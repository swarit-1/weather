"""Environment and constants."""

import os
from pathlib import Path

# Environment
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# NWS API (required by NWS: User-Agent must identify app)
NWS_BASE_URL = os.getenv("NWS_BASE_URL", "https://api.weather.gov")
USER_AGENT = os.getenv("USER_AGENT", "StormOpsConsole")

# LLM (Morph)
MORPH_API_KEY = os.getenv("MORPH_API_KEY", "")
MORPH_BASE_URL = os.getenv("MORPH_BASE_URL", "")
MORPH_MODEL = os.getenv("MORPH_MODEL", "")

# Retrieval
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
