from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from evaluation.safety_corpus_loader import (  # noqa: E402
    SafetyCorpus,
)
from evaluation.safety_evaluator import (  # noqa: E402
    SafetyEvaluator,
)


CORPUS_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "corpus"
    / "safety_cases.json"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "evaluation"
    / "safety_6e.json"
)


def main() -> int:
    corpus = SafetyCorpus.load(
        CORPUS_PATH
    )

    report = SafetyEvaluator.run(
        corpus
    )

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    safety = report[
        "safety"
    ]["summary"]
    routing = report[
        "routing"
    ]["summary"]

    print()
    print("Safety Evaluation")
    print("-----------------")
    print(
        "Cases: "
        f"{safety['case_count']}"
    )
    print(
        "Unsafe block recall: "
        f"{safety['unsafe_block_recall']:.3f}"
    )
    print(
        "Benign false positive rate: "
        f"{safety['benign_false_positive_rate']:.3f}"
    )
    print(
        "Decision accuracy: "
        f"{safety['decision_accuracy']:.3f}"
    )
    print(
        "Blocked category accuracy: "
        f"{safety['blocked_category_accuracy']:.3f}"
    )
    print(
        "Latency mean/median/p95/max: "
        f"{safety['latency']['mean_ms']:.3f} / "
        f"{safety['latency']['median_ms']:.3f} / "
        f"{safety['latency']['p95_ms']:.3f} / "
        f"{safety['latency']['max_ms']:.3f} ms"
    )

    print()
    print("Routing Evaluation")
    print("------------------")
    print(
        "Cases: "
        f"{routing['case_count']}"
    )
    print(
        "Route accuracy: "
        f"{routing['route_accuracy']:.3f}"
    )
    print(
        "Latency mean/median/p95/max: "
        f"{routing['latency']['mean_ms']:.3f} / "
        f"{routing['latency']['median_ms']:.3f} / "
        f"{routing['latency']['p95_ms']:.3f} / "
        f"{routing['latency']['max_ms']:.3f} ms"
    )

    print()
    print(
        "Overall safety gate: "
        + (
            "PASS"
            if report["overall_pass"]
            else "FAIL"
        )
    )
    print()
    print(
        f"Report: {REPORT_PATH}"
    )

    return (
        0
        if report["overall_pass"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )