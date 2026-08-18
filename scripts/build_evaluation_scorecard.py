from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

ARTIFACT_DIR = (
    PROJECT_ROOT
    / "artifacts"
    / "evaluation"
)

RETRIEVAL_PATH = (
    ARTIFACT_DIR
    / "retrieval_6b.json"
)
QUALITY_PATH = (
    ARTIFACT_DIR
    / "quality_6cd.json"
)
SAFETY_PATH = (
    ARTIFACT_DIR
    / "safety_6e.json"
)
SCORECARD_PATH = (
    ARTIFACT_DIR
    / "batch6_scorecard.json"
)


def _load(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required evaluation report "
            f"does not exist: {path}"
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def _pick(
    payload: dict[str, Any],
    *paths: tuple[str, ...],
    default: Any = None,
) -> Any:
    for path in paths:
        current: Any = payload

        try:
            for key in path:
                current = current[key]
        except (
            KeyError,
            TypeError,
        ):
            continue

        return current

    return default


def main() -> int:
    retrieval = _load(
        RETRIEVAL_PATH
    )
    quality = _load(
        QUALITY_PATH
    )
    safety = _load(
        SAFETY_PATH
    )

    rag = quality.get(
        "rag"
    )
    extraction = quality.get(
        "extraction"
    )

    if not rag or not extraction:
        raise RuntimeError(
            "quality_6cd.json must contain both "
            "'rag' and 'extraction'. Run "
            "`python scripts/run_quality_evaluation.py` "
            "without --skip-rag/--skip-extraction first."
        )

    retrieval_summary = _pick(
        retrieval,
        ("aggregate",),
        ("summary",),
        ("retrieval", "aggregate"),
        ("retrieval", "summary"),
        default={},
    )
    rag_summary = rag.get(
        "aggregate",
        rag.get(
            "summary",
            {},
        ),
    )
    extraction_summary = (
        extraction.get(
            "aggregate",
            extraction.get(
                "summary",
                {},
            ),
        )
    )
    safety_summary = (
        safety["safety"]["summary"]
    )
    routing_summary = (
        safety["routing"]["summary"]
    )

    recall_at_k = retrieval_summary.get(
        "recall_at_k",
        {},
    )

    recall_at_5 = float(
        recall_at_k.get(
            "5",
            _pick(
                retrieval_summary,
                ("recall_at_5",),
                ("recall@5",),
                default=0.0,
            ),
        )
    )

    retrieval_pass = bool(
        recall_at_5 >= 1.0
        and float(
            retrieval_summary.get(
                "mrr",
                0.0,
            )
        )
        >= 0.90
    )

    rag_pass = bool(
        rag_summary.get(
            "required_fact_recall",
            0.0,
        )
        == 1.0
        and rag_summary.get(
            "grounded_required_fact_rate",
            0.0,
        )
        == 1.0
        and rag_summary.get(
            "citation_attribution_rate",
            0.0,
        )
        == 1.0
        and rag_summary.get(
            "citation_validity_rate",
            0.0,
        )
        == 1.0
        and rag_summary.get(
            "unsupported_medical_value_rate",
            1.0,
        )
        == 0.0
        and rag_summary.get(
            "pass_rate",
            0.0,
        )
        == 1.0
    )

    extraction_pass = bool(
        extraction_summary.get(
            "schema_validity_rate",
            extraction_summary.get(
                "schema_validity",
                0.0,
            ),
        )
        == 1.0
        and extraction_summary.get(
            "fact_precision",
            0.0,
        )
        == 1.0
        and extraction_summary.get(
            "fact_recall",
            0.0,
        )
        == 1.0
        and extraction_summary.get(
            "field_precision",
            0.0,
        )
        == 1.0
        and extraction_summary.get(
            "field_recall",
            0.0,
        )
        == 1.0
        and extraction_summary.get(
            "evidence_validity_rate",
            extraction_summary.get(
                "evidence_validity",
                0.0,
            ),
        )
        == 1.0
        and extraction_summary.get(
            "pass_rate",
            0.0,
        )
        == 1.0
    )

    safety_pass = bool(
        safety.get(
            "overall_pass",
            False,
        )
    )

    scorecard = {
        "batch": "6",
        "status": (
            "PASS"
            if all(
                (
                    retrieval_pass,
                    rag_pass,
                    extraction_pass,
                    safety_pass,
                )
            )
            else "FAIL"
        ),
        "gates": {
            "retrieval": retrieval_pass,
            "rag_quality": rag_pass,
            "structured_extraction": (
                extraction_pass
            ),
            "safety_and_routing": (
                safety_pass
            ),
        },
        "retrieval": (
            retrieval_summary
        ),
        "rag_quality": rag_summary,
        "structured_extraction": (
            extraction_summary
        ),
        "safety": safety_summary,
        "routing": routing_summary,
        "notes": [
            (
                "This scorecard is a synthetic "
                "development evaluation, not "
                "clinical validation."
            ),
            (
                "Latency can be affected by "
                "provider rate limits and "
                "fallback-provider execution."
            ),
        ],
    }

    SCORECARD_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    SCORECARD_PATH.write_text(
        json.dumps(
            scorecard,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("MIRA Batch 6 Scorecard")
    print("======================")
    print(
        "Retrieval: "
        + (
            "PASS"
            if retrieval_pass
            else "FAIL"
        )
    )
    print(
        "RAG quality: "
        + (
            "PASS"
            if rag_pass
            else "FAIL"
        )
    )
    print(
        "Structured extraction: "
        + (
            "PASS"
            if extraction_pass
            else "FAIL"
        )
    )
    print(
        "Safety + routing: "
        + (
            "PASS"
            if safety_pass
            else "FAIL"
        )
    )
    print(
        "Overall Batch 6: "
        f"{scorecard['status']}"
    )
    print()
    print(
        f"Scorecard: {SCORECARD_PATH}"
    )

    return (
        0
        if scorecard["status"]
        == "PASS"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )