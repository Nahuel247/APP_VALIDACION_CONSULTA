from pathlib import Path

from src.storage.repository import PredictionRepository


def test_repository_upsert_and_vote(tmp_path: Path) -> None:
    db_path = tmp_path / "feedback.db"
    schema_path = tmp_path / "schema.sql"
    schema_path.write_text(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            normalized_text TEXT NOT NULL UNIQUE,
            predicted_label TEXT NOT NULL,
            confidence REAL NOT NULL,
            confidence_valida REAL NOT NULL DEFAULT 0,
            confidence_no_valida REAL NOT NULL DEFAULT 0,
            times_asked INTEGER NOT NULL DEFAULT 1,
            upvotes INTEGER NOT NULL DEFAULT 0,
            downvotes INTEGER NOT NULL DEFAULT 0,
            interactions INTEGER NOT NULL DEFAULT 1,
            is_hidden INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """,
        encoding="utf-8",
    )

    repository = PredictionRepository(db_path=db_path, schema_path=schema_path)
    stored = repository.upsert_prediction(
        question_text="¿Como postulo a una beca municipal?",
        predicted_label="valida",
        confidence=0.93,
        probabilities={"valida": 0.93, "no_valida": 0.07},
    )

    assert stored.predicted_label == "valida"
    assert stored.times_asked == 1

    stored_again = repository.upsert_prediction(
        question_text="¿Como postulo a una beca municipal?",
        predicted_label="valida",
        confidence=0.91,
        probabilities={"valida": 0.91, "no_valida": 0.09},
    )

    assert stored_again.times_asked == 2
    assert stored_again.interactions == 2

    voted = repository.vote(stored_again.id, is_correct=True)
    assert voted.upvotes == 1
    assert voted.interactions == 3
