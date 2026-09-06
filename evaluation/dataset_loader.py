from __future__ import annotations

import json
from pathlib import Path

from evaluation.models import RAGEvalDataset


def load_rag_eval_dataset(path: str | Path) -> RAGEvalDataset:
    dataset_path = Path(path)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: {dataset_path}"
        )

    with dataset_path.open("r", encoding="utf-8") as handle:
        raw_dataset = json.load(handle)

    if not isinstance(raw_dataset, dict):
        raise ValueError(
            "Evaluation dataset root must be a JSON object."
        )

    return RAGEvalDataset.from_dict(raw_dataset)
