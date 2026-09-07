from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_json_report(
    *,
    report: dict[str, Any],
    output_directory: str | Path,
    prefix: str = "rag_retrieval_eval",
) -> Path:
    output_dir = Path(
        output_directory
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = (
        datetime.now(
            timezone.utc
        )
        .strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )

    output_path = (
        output_dir
        / f"{prefix}_{timestamp}.json"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            report,
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")

    return output_path


def dataclass_list(
    values: list,
) -> list[dict]:
    return [
        asdict(value)
        for value in values
    ]
