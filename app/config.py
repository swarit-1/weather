"""Environment configuration and constants."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
NWS_API_BASE_URL = os.getenv("NWS_API_BASE_URL", "https://api.weather.gov")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "default-model")

# Service Configuration
VECTOR_STORE_DIMENSION = int(os.getenv("VECTOR_STORE_DIMENSION", "1536"))
MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "512"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Constants
TEMPERATURE_THRESHOLDS = {
    "extreme_heat": 95,
    "heat": 85,
    "cold": 32,
    "extreme_cold": -10,
}

WIND_SPEED_THRESHOLDS = {
    "high": 20,
    "extreme": 40,
}
