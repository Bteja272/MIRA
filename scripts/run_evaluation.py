from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


def _run(
    relative_script: str,
    *,
    allow_failure: bool = False,
) -> int:
    command = [
        sys.executable,
        str(
            PROJECT_ROOT
            / relative_script
        ),
    ]

    print()
    print(
        "$ "
        + " ".join(command)
    )

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
    )

    if (
        completed.returncode != 0
        and not allow_failure
    ):
        raise subprocess.CalledProcessError(
            completed.returncode,
            command,
        )

    return completed.returncode


def main() -> int:
    # Retrieval corpus/fixture evaluation.
    _run(
        "scripts/run_retrieval_evaluation.py"
    )

    # Run both RAG and extraction so quality_6cd.json contains both
    # sections for the consolidated scorecard.
    _run(
        "scripts/run_quality_evaluation.py"
    )

    # Safety evaluation returns 1 when a regression gate fails. Keep
    # going so the consolidated scorecard is still generated and shows
    # exactly which Batch 6 gate failed.
    safety_return_code = _run(
        "scripts/run_safety_evaluation.py",
        allow_failure=True,
    )

    scorecard_return_code = _run(
        "scripts/build_evaluation_scorecard.py",
        allow_failure=True,
    )

    if (
        safety_return_code != 0
        or scorecard_return_code != 0
    ):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )