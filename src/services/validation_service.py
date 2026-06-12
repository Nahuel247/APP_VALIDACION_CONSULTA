from __future__ import annotations

from src.inference.predictor import MunicipalityQuestionPredictor, PredictionResult
from src.storage.repository import PredictionRepository, StoredPrediction


class QuestionValidationService:
    def __init__(self, predictor: MunicipalityQuestionPredictor, repository: PredictionRepository):
        self.predictor = predictor
        self.repository = repository

    def classify_and_store(self, question_text: str) -> tuple[PredictionResult, StoredPrediction]:
        result = self.predictor.predict(question_text)
        stored = self.repository.upsert_prediction(
            question_text=result.question_text,
            predicted_label=result.predicted_label,
            confidence=result.confidence,
            probabilities=result.probabilities,
        )
        return result, stored

    def vote(self, prediction_id: int, is_correct: bool) -> StoredPrediction:
        return self.repository.vote(prediction_id=prediction_id, is_correct=is_correct)

    def hide_prediction(self, prediction_id: int) -> StoredPrediction:
        return self.repository.hide_prediction(prediction_id=prediction_id)

    def history(self, label_filter: str = "todos", limit: int = 100) -> list[StoredPrediction]:
        return self.repository.list_predictions(label_filter=label_filter, limit=limit)

    def summary(self) -> dict[str, int]:
        return self.repository.summary()
