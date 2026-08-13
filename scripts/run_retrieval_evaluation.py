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
from evaluation.retrieval_evaluator import (  # noqa: E402
    RetrievalEvaluator,
)
from evaluation.retrieval_fixture import (  # noqa: E402
    RetrievalEvaluationFixture,
)


DEFAULT_CORPUS = (
    REPO_ROOT
    / "evaluation"
    / "corpus"
    / "retrieval_corpus.json"
)

DEFAULT_OUTPUT = (
    REPO_ROOT
    / "artifacts"
    / "evaluation"
    / "retrieval_6b.json"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run MIRA synthetic retrieval "
            "evaluation."
        ),
    )

    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--ks",
        nargs="+",
        type=int,
        default=[
            1,
            3,
            5,
        ],
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


def _print_summary(
    report: dict,
) -> None:
    aggregate = report[
        "aggregate"
    ]

    print()
    print(
        "MIRA Retrieval Evaluation"
    )
    print(
        "========================="
    )
    print(
        f"Cases: {report['case_count']}"
    )

    for k in report["ks"]:
        key = str(k)

        print(
            f"Recall@{k}: "
            f"{aggregate['recall_at_k'][key]:.3f}"
        )

        print(
            f"Precision@{k}: "
            f"{aggregate['precision_at_k'][key]:.3f}"
        )

    print(
        f"MRR: {aggregate['mrr']:.3f}"
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

    corpus = EvaluationCorpus.load(
        args.corpus
    )

    print(
        "Resetting isolated synthetic "
        "evaluation fixture..."
    )

    RetrievalEvaluationFixture.reset(
        corpus
    )

    evaluator = RetrievalEvaluator(
        corpus=corpus,
        ks=args.ks,
    )

    print(
        "Warming retrieval models..."
    )

    evaluator.warm_up()

    print(
        "Running retrieval cases..."
    )

    report = evaluator.evaluate()

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

    _print_summary(
        report
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
            corpus
        )


if __name__ == "__main__":
    main()