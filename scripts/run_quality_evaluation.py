from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


from evaluation.corpus_loader import (  # noqa: E402
    EvaluationCorpus,
)
from evaluation.extraction_evaluator import (  # noqa: E402
    ExtractionEvaluator,
)
from evaluation.quality_corpus_loader import (  # noqa: E402
    QualityCorpus,
)
from evaluation.rag_evaluator import (  # noqa: E402
    RAGEvaluator,
)
from evaluation.retrieval_evaluator import (  # noqa: E402
    RetrievalEvaluator,
)
from evaluation.retrieval_fixture import (  # noqa: E402
    RetrievalEvaluationFixture,
)


DEFAULT_RETRIEVAL_CORPUS = (
    REPO_ROOT
    / "evaluation"
    / "corpus"
    / "retrieval_corpus.json"
)

DEFAULT_QUALITY_CORPUS = (
    REPO_ROOT
    / "evaluation"
    / "corpus"
    / "quality_cases.json"
)

DEFAULT_OUTPUT = (
    REPO_ROOT
    / "artifacts"
    / "evaluation"
    / "quality_6cd.json"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run MIRA synthetic RAG and "
            "structured-extraction evaluation."
        ),
    )

    parser.add_argument(
        "--retrieval-corpus",
        type=Path,
        default=(
            DEFAULT_RETRIEVAL_CORPUS
        ),
    )

    parser.add_argument(
        "--quality-corpus",
        type=Path,
        default=(
            DEFAULT_QUALITY_CORPUS
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--skip-rag",
        action="store_true",
    )

    parser.add_argument(
        "--skip-extraction",
        action="store_true",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help=(
            "Remove the isolated synthetic "
            "evaluation fixture after the run."
        ),
    )

    return parser.parse_args()


def _print_rag_summary(
    report: dict,
) -> None:
    if not report.get(
        "aggregate"
    ):
        return

    aggregate = report[
        "aggregate"
    ]

    print()
    print(
        "RAG Quality"
    )
    print(
        "-----------"
    )
    print(
        "Cases: "
        f"{report['case_count']}"
    )
    print(
        "Required fact recall: "
        f"{aggregate['required_fact_recall']:.3f}"
    )
    print(
        "Grounded fact rate: "
        f"{aggregate['grounded_required_fact_rate']:.3f}"
    )
    print(
        "Citation attribution: "
        f"{aggregate['citation_attribution_rate']:.3f}"
    )
    print(
        "Citation validity: "
        f"{aggregate['citation_validity_rate']:.3f}"
    )
    print(
        "Unsupported medical value rate: "
        f"{aggregate['unsupported_medical_value_rate']:.3f}"
    )
    print(
        "Pass rate: "
        f"{aggregate['pass_rate']:.3f}"
    )

    latency = aggregate[
        "latency"
    ]

    print(
        "Latency mean/median/p95/max: "
        f"{latency['mean_ms']:.1f} / "
        f"{latency['median_ms']:.1f} / "
        f"{latency['p95_ms']:.1f} / "
        f"{latency['max_ms']:.1f} ms"
    )


def _print_extraction_summary(
    report: dict,
) -> None:
    if not report.get(
        "aggregate"
    ):
        return

    aggregate = report[
        "aggregate"
    ]

    print()
    print(
        "Structured Extraction"
    )
    print(
        "---------------------"
    )
    print(
        "Cases: "
        f"{report['case_count']}"
    )
    print(
        "Schema validity: "
        f"{aggregate['schema_validity_rate']:.3f}"
    )
    print(
        "Fact precision / recall: "
        f"{aggregate['fact_precision']:.3f} / "
        f"{aggregate['fact_recall']:.3f}"
    )
    print(
        "Field precision / recall: "
        f"{aggregate['field_precision']:.3f} / "
        f"{aggregate['field_recall']:.3f}"
    )
    print(
        "Completeness: "
        f"{aggregate['completeness']:.3f}"
    )
    print(
        "Evidence validity: "
        f"{aggregate['evidence_validity_rate']:.3f}"
    )
    print(
        "Pass rate: "
        f"{aggregate['pass_rate']:.3f}"
    )

    latency = aggregate[
        "latency"
    ]

    print(
        "Latency mean/median/p95/max: "
        f"{latency['mean_ms']:.1f} / "
        f"{latency['median_ms']:.1f} / "
        f"{latency['p95_ms']:.1f} / "
        f"{latency['max_ms']:.1f} ms"
    )


def main() -> None:
    args = _parse_args()

    retrieval_corpus = (
        EvaluationCorpus.load(
            args.retrieval_corpus
        )
    )

    quality_corpus = (
        QualityCorpus.load(
            args.quality_corpus,
            retrieval_corpus=(
                retrieval_corpus
            ),
        )
    )

    print(
        "Resetting isolated synthetic "
        "evaluation fixture..."
    )

    RetrievalEvaluationFixture.reset(
        retrieval_corpus
    )

    # Warm only the local retrieval models. This avoids adding an
    # unnecessary LLM request solely for benchmark warm-up.
    retrieval_warmup = (
        RetrievalEvaluator(
            corpus=retrieval_corpus,
            ks=[3],
        )
    )

    print(
        "Warming retrieval models..."
    )

    retrieval_warmup.warm_up()

    user_id = (
        retrieval_corpus
        .evaluation_user[
            "user_id"
        ]
    )

    rag_report = {
        "case_count": 0,
        "aggregate": {},
        "cases": [],
    }

    extraction_report = {
        "case_count": 0,
        "aggregate": {},
        "cases": [],
    }

    if not args.skip_rag:
        print(
            "Running RAG quality cases..."
        )

        rag_report = (
            RAGEvaluator(
                corpus=(
                    quality_corpus
                ),
                retrieval_corpus=(
                    retrieval_corpus
                ),
                user_id=user_id,
            )
            .evaluate()
        )

    if not args.skip_extraction:
        print(
            "Running structured "
            "extraction cases..."
        )

        extraction_report = (
            ExtractionEvaluator(
                quality_corpus=(
                    quality_corpus
                ),
                retrieval_corpus=(
                    retrieval_corpus
                ),
                user_id=user_id,
            )
            .evaluate()
        )

    report = {
        "quality_corpus_version": (
            quality_corpus.version
        ),
        "rag": rag_report,
        "extraction": (
            extraction_report
        ),
    }

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            report,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    _print_rag_summary(
        rag_report
    )

    _print_extraction_summary(
        extraction_report
    )

    print()
    print(
        f"Report: {args.output}"
    )

    if args.cleanup:
        print(
            "Cleaning synthetic "
            "evaluation fixture..."
        )

        RetrievalEvaluationFixture.cleanup(
            retrieval_corpus
        )


if __name__ == "__main__":
    main()