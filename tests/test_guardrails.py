from src.inference.guardrails import apply_guardrails


def test_guardrail_blocks_explicit_obscenity() -> None:
    result = apply_guardrails("a que hora abren el orto?")

    assert result is not None
    assert result.predicted_label == "no_valida"
    assert result.applied_rule == "lenguaje_obsceno"
    assert result.probabilities == {"valida": 0.0, "no_valida": 1.0}


def test_guardrail_does_not_block_valid_municipal_question() -> None:
    result = apply_guardrails("a que hora abren la municipalidad?")

    assert result is None


def test_guardrail_blocks_explicit_sexual_content() -> None:
    result = apply_guardrails("lo chupas?")

    assert result is not None
    assert result.predicted_label == "no_valida"
    assert result.applied_rule == "contenido_sexual"
    assert result.probabilities == {"valida": 0.0, "no_valida": 1.0}
