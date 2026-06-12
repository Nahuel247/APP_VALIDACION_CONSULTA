from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from huggingface_hub import snapshot_download
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.config import MAX_TEXT_LENGTH, MODEL_CACHE_DIR, MODEL_REPO_ID, MODEL_REVISION


@dataclass(slots=True)
class PredictionResult:
    question_text: str
    predicted_label: str
    confidence: float
    probabilities: dict[str, float]


class MunicipalityQuestionPredictor:
    def __init__(self, model_dir: Path):
        self.model_dir = self._resolve_model_dir(Path(model_dir))

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir), local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            str(self.model_dir),
            local_files_only=True,
        )
        self.model.to(self.device)
        self.model.eval()
        self.id2label = self._load_labels()

    @staticmethod
    def _has_model_artifacts(model_dir: Path) -> bool:
        required_files = ("config.json", "model.safetensors", "tokenizer.json")
        return model_dir.exists() and all((model_dir / filename).exists() for filename in required_files)

    def _resolve_model_dir(self, model_dir: Path) -> Path:
        if self._has_model_artifacts(model_dir):
            return model_dir

        if MODEL_REPO_ID:
            target_dir = MODEL_CACHE_DIR / MODEL_REPO_ID.replace("/", "__")
            if not self._has_model_artifacts(target_dir):
                snapshot_download(
                    repo_id=MODEL_REPO_ID,
                    revision=MODEL_REVISION,
                    local_dir=str(target_dir),
                    local_dir_use_symlinks=False,
                    ignore_patterns=[
                        "*.bin",
                        "optimizer.pt",
                        "scheduler.pt",
                        "rng_state.pth",
                        "trainer_state.json",
                        "training_args.bin",
                        "checkpoints/*",
                    ],
                )
            if self._has_model_artifacts(target_dir):
                return target_dir

        raise FileNotFoundError(
            "No se encontro un modelo utilizable. "
            f"Se busco en '{model_dir}' y no hubo descarga disponible desde MODEL_REPO_ID."
        )

    def _load_labels(self) -> dict[int, str]:
        labels_path = self.model_dir / "labels.json"
        if labels_path.exists():
            with open(labels_path, "r", encoding="utf-8") as file:
                payload = json.load(file)
            return {int(key): value for key, value in payload["id2label"].items()}

        config_mapping = getattr(self.model.config, "id2label", None)
        if config_mapping:
            return {int(key): value for key, value in config_mapping.items()}

        raise ValueError("No se pudieron cargar etiquetas desde labels.json ni desde config.id2label")

    def predict(self, question_text: str) -> PredictionResult:
        cleaned_text = " ".join(question_text.split()).strip()
        if not cleaned_text:
            raise ValueError("La pregunta no puede estar vacia.")

        encoded = self.tokenizer(
            cleaned_text,
            truncation=True,
            max_length=MAX_TEXT_LENGTH,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}

        with torch.no_grad():
            outputs = self.model(**encoded)
            probabilities_tensor = torch.softmax(outputs.logits, dim=-1).squeeze(0).cpu()

        probabilities = {
            self.id2label[index]: float(score)
            for index, score in enumerate(probabilities_tensor.tolist())
        }
        predicted_index = int(torch.argmax(probabilities_tensor).item())
        predicted_label = self.id2label[predicted_index]

        return PredictionResult(
            question_text=cleaned_text,
            predicted_label=predicted_label,
            confidence=probabilities[predicted_label],
            probabilities=probabilities,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "model_dir": str(self.model_dir),
            "device": str(self.device),
            "labels": list(self.id2label.values()),
            "model_repo_id": MODEL_REPO_ID,
        }
