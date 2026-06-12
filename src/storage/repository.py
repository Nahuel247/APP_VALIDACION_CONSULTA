from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class StoredPrediction:
    id: int
    question_text: str
    normalized_text: str
    predicted_label: str
    confidence: float
    confidence_valida: float
    confidence_no_valida: float
    times_asked: int
    upvotes: int
    downvotes: int
    interactions: int
    is_hidden: int
    created_at: str
    updated_at: str


class PredictionRepository:
    def __init__(self, db_path: Path, schema_path: Path):
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        schema = self.schema_path.read_text(encoding="utf-8")
        with self._connect() as connection:
            connection.executescript(schema)
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(predictions)").fetchall()
            }
            if "is_hidden" not in columns:
                connection.execute(
                    "ALTER TABLE predictions ADD COLUMN is_hidden INTEGER NOT NULL DEFAULT 0"
                )
            connection.commit()

    @staticmethod
    def normalize_text(question_text: str) -> str:
        return " ".join(question_text.lower().split())

    @staticmethod
    def _utcnow() -> str:
        return datetime.now(timezone.utc).isoformat()

    def upsert_prediction(
        self,
        question_text: str,
        predicted_label: str,
        confidence: float,
        probabilities: dict[str, float],
    ) -> StoredPrediction:
        normalized_text = self.normalize_text(question_text)
        now = self._utcnow()
        confidence_valida = float(probabilities.get("valida", 0.0))
        confidence_no_valida = float(probabilities.get("no_valida", 0.0))

        with self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM predictions WHERE normalized_text = ?",
                (normalized_text,),
            ).fetchone()

            if existing:
                connection.execute(
                    """
                    UPDATE predictions
                    SET question_text = ?,
                        predicted_label = ?,
                        confidence = ?,
                        confidence_valida = ?,
                        confidence_no_valida = ?,
                        times_asked = times_asked + 1,
                        interactions = interactions + 1,
                        updated_at = ?
                    WHERE normalized_text = ?
                    """,
                    (
                        question_text,
                        predicted_label,
                        confidence,
                        confidence_valida,
                        confidence_no_valida,
                        now,
                        normalized_text,
                    ),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO predictions (
                        question_text,
                        normalized_text,
                        predicted_label,
                        confidence,
                        confidence_valida,
                        confidence_no_valida,
                        times_asked,
                        upvotes,
                        downvotes,
                        interactions,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, 0, 0, 1, ?, ?)
                    """,
                    (
                        question_text,
                        normalized_text,
                        predicted_label,
                        confidence,
                        confidence_valida,
                        confidence_no_valida,
                        now,
                        now,
                    ),
                )
            connection.commit()

        return self.get_by_normalized_text(normalized_text)

    def get_by_normalized_text(self, normalized_text: str) -> StoredPrediction:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM predictions WHERE normalized_text = ?",
                (normalized_text,),
            ).fetchone()
        if row is None:
            raise KeyError(f"No existe registro para: {normalized_text}")
        return self._row_to_prediction(row)

    def vote(self, prediction_id: int, is_correct: bool) -> StoredPrediction:
        column = "upvotes" if is_correct else "downvotes"
        now = self._utcnow()
        with self._connect() as connection:
            connection.execute(
                f"UPDATE predictions SET {column} = {column} + 1, interactions = interactions + 1, updated_at = ? WHERE id = ?",
                (now, prediction_id),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM predictions WHERE id = ?",
                (prediction_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"No existe registro con id={prediction_id}")
        return self._row_to_prediction(row)

    def hide_prediction(self, prediction_id: int) -> StoredPrediction:
        now = self._utcnow()
        with self._connect() as connection:
            connection.execute(
                "UPDATE predictions SET is_hidden = 1, updated_at = ? WHERE id = ?",
                (now, prediction_id),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM predictions WHERE id = ?",
                (prediction_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"No existe registro con id={prediction_id}")
        return self._row_to_prediction(row)

    def list_predictions(
        self,
        label_filter: str | None = None,
        limit: int = 100,
        include_hidden: bool = False,
    ) -> list[StoredPrediction]:
        query = "SELECT * FROM predictions"
        params: list[object] = []
        conditions: list[str] = []

        if not include_hidden:
            conditions.append("is_hidden = 0")
        if label_filter and label_filter != "todos":
            conditions.append("predicted_label = ?")
            params.append(label_filter)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY interactions DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._row_to_prediction(row) for row in rows]

    def summary(self) -> dict[str, int]:
        with self._connect() as connection:
            total = connection.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
            validas = connection.execute(
                "SELECT COUNT(*) FROM predictions WHERE predicted_label = 'valida'"
            ).fetchone()[0]
            no_validas = connection.execute(
                "SELECT COUNT(*) FROM predictions WHERE predicted_label = 'no_valida'"
            ).fetchone()[0]
            interacciones = connection.execute(
                "SELECT COALESCE(SUM(interactions), 0) FROM predictions"
            ).fetchone()[0]
            ocultas = connection.execute(
                "SELECT COUNT(*) FROM predictions WHERE is_hidden = 1"
            ).fetchone()[0]
        return {
            "total_preguntas": int(total),
            "validas": int(validas),
            "no_validas": int(no_validas),
            "interacciones": int(interacciones),
            "ocultas": int(ocultas),
        }

    @staticmethod
    def _row_to_prediction(row: sqlite3.Row) -> StoredPrediction:
        return StoredPrediction(**dict(row))
