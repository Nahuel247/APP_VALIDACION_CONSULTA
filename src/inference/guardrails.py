from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GuardrailResult:
    predicted_label: str
    probabilities: dict[str, float]
    applied_rule: str


OBSCENE_PATTERNS = (
    r"\borto\b",
    r"\bculia[doars]?\b",
    r"\bculiao\b",
    r"\bculi[aeo]?\b",
    r"\bctm\b",
    r"\bconcha(?:sumadre)?\b",
    r"\bpichula\b",
    r"\bpene\b",
    r"\bporno\b",
    r"\bsexual\b",
    r"\bsemen\b",
    r"\btetas?\b",
    r"\bweon(?:es)?\b",
    r"\bhueon(?:es)?\b",
    r"\bwn\b",
)

SEXUAL_PATTERNS = (
    r"\bchupa(?:r|s|la|lo|le|las|los)?\b",
)


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents).strip()


def apply_guardrails(question_text: str) -> GuardrailResult | None:
    normalized_text = _normalize_text(question_text)

    for pattern in OBSCENE_PATTERNS:
        if re.search(pattern, normalized_text):
            return GuardrailResult(
                predicted_label="no_valida",
                probabilities={"valida": 0.0, "no_valida": 1.0},
                applied_rule="lenguaje_obsceno",
            )

    for pattern in SEXUAL_PATTERNS:
        if re.search(pattern, normalized_text):
            return GuardrailResult(
                predicted_label="no_valida",
                probabilities={"valida": 0.0, "no_valida": 1.0},
                applied_rule="contenido_sexual",
            )

    return None
