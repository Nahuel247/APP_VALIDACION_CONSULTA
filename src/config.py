from __future__ import annotations

import os
from pathlib import Path

try:
    import streamlit as st
    from streamlit.errors import StreamlitSecretNotFoundError
except Exception:  # pragma: no cover - Streamlit may be unavailable in tests
    st = None
    StreamlitSecretNotFoundError = Exception


def get_setting(name: str, default: str | None = None) -> str | None:
    env_value = os.getenv(name)
    if env_value is not None:
        return env_value

    if st is None:
        return default

    try:
        secret_value = st.secrets.get(name)
    except StreamlitSecretNotFoundError:
        secret_value = None

    if secret_value is None:
        return default
    return str(secret_value)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATASET_PATH = DATA_DIR / "raw" / "municipio_validacion_preguntas_400.csv"
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models" / "municipio_question_validator"
MODEL_DIR = Path(get_setting("MODEL_DIR", str(DEFAULT_MODEL_DIR)))
MODEL_REPO_ID = get_setting("MODEL_REPO_ID")
MODEL_REVISION = get_setting("MODEL_REVISION", "main") or "main"
MODEL_CACHE_DIR = Path(get_setting("MODEL_CACHE_DIR", str(DATA_DIR / "model_cache")))
DATABASE_PATH = Path(get_setting("DATABASE_PATH", str(DATA_DIR / "feedback.db")))
APP_TITLE = get_setting("APP_TITLE", "Validador de Preguntas para Chatbot Municipal") or "Validador de Preguntas para Chatbot Municipal"
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
