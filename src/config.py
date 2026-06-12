from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATASET_PATH = DATA_DIR / "raw" / "municipio_validacion_preguntas_400.csv"
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models" / "municipio_question_validator"
MODEL_DIR = Path(os.getenv("MODEL_DIR", DEFAULT_MODEL_DIR))
MODEL_REPO_ID = os.getenv("MODEL_REPO_ID")
MODEL_REVISION = os.getenv("MODEL_REVISION", "main")
MODEL_CACHE_DIR = Path(os.getenv("MODEL_CACHE_DIR", DATA_DIR / "model_cache"))
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", DATA_DIR / "feedback.db"))
APP_TITLE = os.getenv("APP_TITLE", "Validador de Preguntas para Chatbot Municipal")
MAX_TEXT_LENGTH = 512
DEFAULT_HISTORY_LIMIT = 100

LABEL_DISPLAY = {
    "valida": "Valida",
    "no_valida": "No valida",
}

LABEL_COLOR = {
    "valida": "#0f766e",
    "no_valida": "#b91c1c",
}


def ensure_data_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
