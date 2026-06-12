from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def seed_env_from_streamlit_secrets() -> None:
    for key in ("MODEL_REPO_ID", "MODEL_REVISION", "MODEL_CACHE_DIR"):
        if os.getenv(key):
            continue
        try:
            value = st.secrets.get(key)
        except StreamlitSecretNotFoundError:
            value = None
        if value:
            os.environ[key] = str(value)


seed_env_from_streamlit_secrets()

from src.config import (  # noqa: E402
    APP_TITLE,
    DATABASE_PATH,
    DEFAULT_HISTORY_LIMIT,
    LABEL_COLOR,
    LABEL_DISPLAY,
    MODEL_DIR,
    ensure_data_directories,
)
from src.inference.predictor import MunicipalityQuestionPredictor  # noqa: E402
from src.services.validation_service import QuestionValidationService  # noqa: E402
from src.storage.repository import PredictionRepository  # noqa: E402


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def label_badge(label: str) -> str:
    color = LABEL_COLOR.get(label, "#334155")
    text = LABEL_DISPLAY.get(label, label)
    return (
        f"<span style='background:{color};color:white;padding:0.35rem 0.6rem;"
        "border-radius:999px;font-size:0.85rem;font-weight:600;'>"
        f"{text}</span>"
    )


def vote_percentages(upvotes: int, downvotes: int) -> tuple[float, float, int]:
    total_votes = upvotes + downvotes
    if total_votes == 0:
        return 0.0, 0.0, 0
    return upvotes / total_votes, downvotes / total_votes, total_votes


def get_admin_password() -> str | None:
    try:
        return st.secrets.get("ADMIN_PASSWORD")
    except StreamlitSecretNotFoundError:
        return None


def admin_mode_enabled() -> bool:
    admin_password = get_admin_password()
    if not admin_password:
        st.session_state["admin_authenticated"] = False
        return False

    return bool(st.session_state.get("admin_authenticated", False))


@st.cache_resource(show_spinner=False)
def get_service() -> QuestionValidationService:
    ensure_data_directories()
    predictor = MunicipalityQuestionPredictor(MODEL_DIR)
    repository = PredictionRepository(
        db_path=DATABASE_PATH,
        schema_path=PROJECT_ROOT / "src" / "storage" / "schema.sql",
    )
    return QuestionValidationService(predictor=predictor, repository=repository)


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏛️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stButton > button[kind="primary"] {
        background: #0f766e;
        border: 1px solid #0f766e;
        color: white;
    }
    .stButton > button[kind="primary"]:hover {
        background: #115e59;
        border-color: #115e59;
        color: white;
    }
    .stButton > button[kind="primary"]:focus {
        box-shadow: 0 0 0 0.2rem rgba(15, 118, 110, 0.2);
        color: white;
    }
    .stButton > button {
        border-radius: 999px;
        border: 1px solid #cbd5e1;
        background: #e2e8f0;
        color: #1e293b;
        font-weight: 700;
    }
    .stButton > button:hover {
        border-color: #94a3b8;
        background: #cbd5e1;
        color: #0f172a;
    }
    .vote-card {
        padding: 1rem 1rem 0.95rem 1rem;
        border: 1px solid #dbe4f0;
        border-radius: 20px;
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
    }
    .vote-card-title {
        margin: 0;
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
    }
    .vote-card-meta {
        margin: 0.3rem 0 0 0;
        color: #475569;
        font-size: 0.88rem;
    }
    .vote-card-label-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-top: 0.7rem;
        font-size: 0.84rem;
        color: #334155;
        font-weight: 600;
    }
    .vote-card-label-strong {
        color: #0f172a;
    }
    .vote-card-bar {
        margin-top: 0.38rem;
        width: 100%;
        height: 10px;
        background: #e8edf5;
        border-radius: 999px;
        overflow: hidden;
        display: flex;
    }
    .vote-card-bar-positive {
        height: 100%;
        background: linear-gradient(90deg, #38bdf8 0%, #2563eb 100%);
    }
    .vote-card-bar-negative {
        height: 100%;
        background: linear-gradient(90deg, #fca5a5 0%, #dc2626 100%);
    }
    .vote-card-stats {
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin-top: 0.75rem;
    }
    .vote-stat-chip {
        padding: 0.34rem 0.62rem;
        border-radius: 999px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        font-size: 0.8rem;
        color: #475569;
    }
    .vote-card-percent {
        margin: 0;
        font-size: 0.9rem;
        color: #0f172a;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

summary = None
metadata = None
is_admin = admin_mode_enabled()

try:
    service = get_service()
except FileNotFoundError as exc:
    st.title(APP_TITLE)
    st.error("No fue posible cargar el modelo para iniciar la aplicacion.")
    st.markdown(
        """
        Revisa esta configuracion en Streamlit Community Cloud:

        ```toml
        MODEL_REPO_ID = "tu-usuario/tu-modelo"
        MODEL_REVISION = "main"
        ADMIN_PASSWORD = "tu-clave-segura"
        ```

        Si no usaras Hugging Face, entonces debes incluir un modelo local utilizable en la ruta configurada por `MODEL_DIR`.
        """
    )
    st.code(str(exc))
    st.stop()

summary = service.summary()
metadata = service.predictor.metadata()

st.title(APP_TITLE)
st.caption(
    "Clasifica preguntas para un chatbot municipal en `valida` o `no_valida`, "
    "guarda el historial y permite feedback colaborativo."
)

with st.sidebar:
    st.subheader("Estado del sistema")
    st.metric("Preguntas registradas", summary["total_preguntas"])
    st.metric("Interacciones acumuladas", summary["interacciones"])
    st.metric("Ocultas del historial", summary.get("ocultas", 0))
    st.divider()
    st.subheader("Modo administrador")
    admin_password = get_admin_password()
    if admin_password:
        if is_admin:
            st.success("Modo administrador activo")
            if st.button("Cerrar modo administrador", use_container_width=True):
                st.session_state["admin_authenticated"] = False
                st.rerun()
        else:
            entered_password = st.text_input(
                "Contrasena",
                type="password",
                key="admin_password_input",
            )
            if st.button("Activar modo administrador", use_container_width=True):
                if entered_password == admin_password:
                    st.session_state["admin_authenticated"] = True
                    st.rerun()
                else:
                    st.error("Contrasena incorrecta.")

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Preguntas validas", summary["validas"])
metric_2.metric("Preguntas no validas", summary["no_validas"])
metric_3.metric("Total registradas", summary["total_preguntas"])

main_tab, history_tab, about_tab = st.tabs(["Clasificar", "Historial y votos", "Acerca del proyecto"])

with main_tab:
    st.subheader("Probar el modelo")
    question_text = st.text_area(
        "Escribe una pregunta para el chatbot municipal",
        placeholder="Ejemplo: ¿Cómo postulo a una beca municipal?",
        height=120,
    )

    if st.button("Clasificar pregunta", type="primary", use_container_width=True):
        if not question_text.strip():
            st.warning("Ingresa una pregunta antes de clasificar.")
        else:
            try:
                result, stored = service.classify_and_store(question_text)
            except Exception as exc:  # pragma: no cover - feedback visual
                st.error(f"No fue posible clasificar la pregunta: {exc}")
            else:
                st.success("Clasificacion realizada correctamente.")
                st.markdown(
                    f"""
                    <div style="padding:1rem;border:1px solid #dbe4f0;border-radius:16px;background:#f8fafc;">
                        <p style="margin:0 0 0.75rem 0;font-size:0.95rem;color:#334155;">Pregunta</p>
                        <p style="margin:0 0 1rem 0;font-size:1.1rem;font-weight:600;color:#0f172a;">{result.question_text}</p>
                        <div style="display:flex;gap:0.75rem;align-items:center;flex-wrap:wrap;">
                            {label_badge(result.predicted_label)}
                            <span style="font-size:0.95rem;color:#334155;">Confianza: <strong>{format_percent(result.confidence)}</strong></span>
                            <span style="font-size:0.95rem;color:#334155;">Interacciones acumuladas: <strong>{stored.interactions}</strong></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                col_a, col_b = st.columns(2)
                col_a.metric("Probabilidad valida", format_percent(result.probabilities.get("valida", 0.0)))
                col_b.metric("Probabilidad no valida", format_percent(result.probabilities.get("no_valida", 0.0)))
                if result.applied_rule:
                    st.caption(f"Regla aplicada: `{result.applied_rule}`")

                current_vote_state_key = f"voted_{stored.id}"
                current_disable_vote = bool(st.session_state.get(current_vote_state_key, False))
                st.caption("Tu voto ayuda a validar si esta clasificacion fue correcta.")
                main_vote_col_1, main_vote_col_2 = st.columns(2)
                if main_vote_col_1.button(
                    "👍 A favor de la clasificacion",
                    key=f"main_upvote_{stored.id}",
                    disabled=current_disable_vote,
                    use_container_width=True,
                ):
                    service.vote(stored.id, is_correct=True)
                    st.session_state[current_vote_state_key] = True
                    st.rerun()
                if main_vote_col_2.button(
                    "👎 En contra de la clasificacion",
                    key=f"main_downvote_{stored.id}",
                    disabled=current_disable_vote,
                    use_container_width=True,
                ):
                    service.vote(stored.id, is_correct=False)
                    st.session_state[current_vote_state_key] = True
                    st.rerun()

                if current_disable_vote:
                    st.caption("Ya registraste un voto en esta sesion para esta pregunta.")

with history_tab:
    st.subheader("Historial guardado")
    filter_col, limit_col = st.columns([1, 1])
    label_filter = filter_col.selectbox(
        "Filtrar por etiqueta",
        options=["todos", "valida", "no_valida"],
        format_func=lambda value: "Todos" if value == "todos" else LABEL_DISPLAY.get(value, value),
    )
    limit = limit_col.slider("Cantidad maxima", min_value=10, max_value=200, value=DEFAULT_HISTORY_LIMIT, step=10)

    history = service.history(label_filter=label_filter, limit=limit)

    if not history:
        st.info("Todavia no hay preguntas registradas.")
    else:
        st.caption("Ordenado de mayor a menor por numero de interacciones.")
        for item in history:
            vote_state_key = f"voted_{item.id}"
            upvote_ratio, downvote_ratio, total_votes = vote_percentages(item.upvotes, item.downvotes)
            disable_vote = bool(st.session_state.get(vote_state_key, False))
            positive_width = upvote_ratio * 100
            negative_width = downvote_ratio * 100

            st.markdown(
                f"""
                <div class="vote-card">
                    <p class="vote-card-title">{item.question_text} <span style="font-weight:600;color:#64748b;">({total_votes} votos)</span></p>
                    <p class="vote-card-meta">
                        {LABEL_DISPLAY.get(item.predicted_label, item.predicted_label)} ·
                        Confianza {format_percent(item.confidence)}
                    </p>
                    <div class="vote-card-label-row">
                        <span><span class="vote-card-label-strong">👍 A favor</span> {format_percent(upvote_ratio)}</span>
                        <span><span class="vote-card-label-strong">👎 En contra</span> {format_percent(downvote_ratio)}</span>
                    </div>
                    <div class="vote-card-bar">
                        <div class="vote-card-bar-positive" style="width:{positive_width}%;"></div>
                        <div class="vote-card-bar-negative" style="width:{negative_width}%;"></div>
                    </div>
                    <div class="vote-card-stats">
                        <span class="vote-stat-chip">A favor: {item.upvotes}</span>
                        <span class="vote-stat-chip">En contra: {item.downvotes}</span>
                        <span class="vote-stat-chip">Veces preguntada: {item.times_asked}</span>
                        <span class="vote-stat-chip">Interacciones: {item.interactions}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            actions_col_1, actions_col_2 = st.columns(2)
            if actions_col_1.button("👍 A favor", key=f"upvote_{item.id}", disabled=disable_vote, use_container_width=True):
                service.vote(item.id, is_correct=True)
                st.session_state[vote_state_key] = True
                st.rerun()
            if actions_col_2.button("👎 En contra", key=f"downvote_{item.id}", disabled=disable_vote, use_container_width=True):
                service.vote(item.id, is_correct=False)
                st.session_state[vote_state_key] = True
                st.rerun()

            if is_admin:
                if st.button(
                    "Ocultar del historial",
                    key=f"hide_{item.id}",
                    use_container_width=True,
                ):
                    service.hide_prediction(item.id)
                    st.rerun()

            if disable_vote:
                st.caption("Ya registraste un voto en esta sesion para esta pregunta.")

with about_tab:
    st.subheader("Que evalua este modelo")
    st.write(
        "El modelo intenta determinar si una pregunta esta dentro del dominio de un chatbot municipal."
    )
    st.markdown(
        "- **Valida**: consulta sobre tramites, beneficios, servicios, horarios, oficinas u otras gestiones municipales.\n"
        "- **No valida**: pregunta fuera de dominio, uso tipo ChatGPT, peticion de informacion sensible o intento de prompt injection."
    )
    st.subheader("Limitaciones")
    st.markdown(
        "- Puede fallar en preguntas ambiguas o muy parecidas a consultas municipales.\n"
        "- Esta version no tiene autenticacion ni moderacion.\n"
        "- El feedback se guarda localmente en SQLite y es ideal para demo o validacion inicial."
    )
    st.subheader("Recursos")
    st.write(f"Dataset de referencia: `data/raw/municipio_validacion_preguntas_400.csv`")
    st.write("Repositorio de entrenamiento: agrega aqui el enlace cuando lo publiques.")
    st.write("Descarga del modelo: agrega aqui el enlace publico si luego lo subes a Hugging Face u otro host.")
