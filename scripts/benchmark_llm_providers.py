#!/usr/bin/env python3

import argparse
import json
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from app.schemas.medical_extraction_strict_schema import (
    MEDICAL_EXTRACTION_CANDIDATE_STRICT_SCHEMA,
)
from app.services.llm_providers.base import (
    LLMProviderError,
    LLMRequest,
)
from app.services.llm_providers.factory import (
    LLMProviderFactory,
)


DIRECT_SYSTEM_PROMPT = (
    "You provide concise educational medical information. "
    "Do not diagnose or recommend treatment."
)

DIRECT_PROMPT = (
    "In one sentence, explain what hemoglobin is."
)

STRUCTURED_SYSTEM_PROMPT = (
    "Extract only explicitly stated facts from the synthetic "
    "medical text. Return one JSON object matching the supplied "
    "schema. Copy factual text exactly. Use lowercase schema enum "
    "tokens for status and flag fields. Do not infer diagnoses or "
    "treatment recommendations."
)

STRUCTURED_PROMPT = """
Synthetic medical document:

Patient: Benchmark Patient
Document Date: March 12, 2026
Provider: Dr. Example

Lab Results:
Hemoglobin A1c: 7.2 %
Reference Range: 4.0 - 5.6 %
Flag: High
Collected: March 12, 2026

Return the structured extraction.
""".strip()


@dataclass(frozen=True)
class BenchmarkRecord:
    provider: str
    mode: str
    run: int
    success: bool
    latency_ms: float
    response_characters: int
    error_kind: str | None = None
    status_code: int | None = None
    error_code: str | None = None


def _percentile_95(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    index = max(
        0,
        int(
            round(
                0.95
                * (len(ordered) - 1)
            )
        ),
    )

    return ordered[index]


def _request_for_mode(
    mode: str,
) -> LLMRequest:
    if mode == "direct":
        return LLMRequest(
            prompt=DIRECT_PROMPT,
            system_prompt=(
                DIRECT_SYSTEM_PROMPT
            ),
            timeout_seconds=120,
            temperature=0.0,
            max_output_tokens=100,
        )

    if mode == "structured":
        return LLMRequest(
            prompt=STRUCTURED_PROMPT,
            system_prompt=(
                STRUCTURED_SYSTEM_PROMPT
            ),
            timeout_seconds=180,
            json_mode=True,
            temperature=0.0,
            max_output_tokens=1000,
            json_schema=(
                MEDICAL_EXTRACTION_CANDIDATE_STRICT_SCHEMA
            ),
        )

    raise ValueError(
        f"Unsupported benchmark mode: {mode}"
    )


def run_benchmark(
    *,
    providers: list[str],
    modes: list[str],
    runs: int,
) -> list[BenchmarkRecord]:
    records: list[BenchmarkRecord] = []

    for provider_name in providers:
        provider = (
            LLMProviderFactory.create(
                provider_name
            )
        )

        for mode in modes:
            request = _request_for_mode(
                mode
            )

            for run_number in range(
                1,
                runs + 1,
            ):
                started_at = perf_counter()

                try:
                    response = (
                        provider.generate(
                            request
                        )
                    )

                except LLMProviderError as exc:
                    elapsed_ms = (
                        perf_counter()
                        - started_at
                    ) * 1000

                    records.append(
                        BenchmarkRecord(
                            provider=(
                                provider_name
                            ),
                            mode=mode,
                            run=run_number,
                            success=False,
                            latency_ms=(
                                elapsed_ms
                            ),
                            response_characters=0,
                            error_kind=(
                                exc.kind
                            ),
                            status_code=(
                                exc.status_code
                            ),
                            error_code=(
                                exc.error_code
                            ),
                        )
                    )

                    print(
                        f"{provider_name:8} "
                        f"{mode:10} "
                        f"run={run_number} "
                        f"FAILED "
                        f"{elapsed_ms:.1f} ms "
                        f"kind={exc.kind} "
                        f"status={exc.status_code}"
                    )

                    continue

                elapsed_ms = (
                    perf_counter()
                    - started_at
                ) * 1000

                records.append(
                    BenchmarkRecord(
                        provider=provider_name,
                        mode=mode,
                        run=run_number,
                        success=True,
                        latency_ms=elapsed_ms,
                        response_characters=(
                            len(response)
                        ),
                    )
                )

                print(
                    f"{provider_name:8} "
                    f"{mode:10} "
                    f"run={run_number} "
                    f"OK "
                    f"{elapsed_ms:.1f} ms "
                    f"chars={len(response)}"
                )

    return records


def summarize(
    records: list[BenchmarkRecord],
) -> list[dict[str, Any]]:
    summary: list[
        dict[str, Any]
    ] = []

    groups = sorted(
        {
            (
                record.provider,
                record.mode,
            )
            for record in records
        }
    )

    for provider, mode in groups:
        matching = [
            record
            for record in records
            if (
                record.provider
                == provider
                and record.mode == mode
            )
        ]

        successful = [
            record.latency_ms
            for record in matching
            if record.success
        ]

        failed_count = sum(
            1
            for record in matching
            if not record.success
        )

        row: dict[str, Any] = {
            "provider": provider,
            "mode": mode,
            "runs": len(matching),
            "successes": (
                len(successful)
            ),
            "failures": failed_count,
        }

        if successful:
            row.update(
                {
                    "mean_ms": round(
                        statistics.mean(
                            successful
                        ),
                        3,
                    ),
                    "median_ms": round(
                        statistics.median(
                            successful
                        ),
                        3,
                    ),
                    "p95_ms": round(
                        _percentile_95(
                            successful
                        ),
                        3,
                    ),
                }
            )

        summary.append(row)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark MIRA LLM providers "
            "using synthetic prompts only."
        )
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        default=[
            "groq",
            "ollama",
        ],
        choices=[
            "groq",
            "ollama",
        ],
    )
    parser.add_argument(
        "--mode",
        choices=[
            "direct",
            "structured",
            "both",
        ],
        default="both",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--json-output",
        default="",
        help=(
            "Optional path for machine-readable "
            "benchmark results."
        ),
    )

    args = parser.parse_args()

    if args.runs <= 0:
        raise SystemExit(
            "--runs must be greater than zero."
        )

    modes = (
        [
            "direct",
            "structured",
        ]
        if args.mode == "both"
        else [args.mode]
    )

    records = run_benchmark(
        providers=args.providers,
        modes=modes,
        runs=args.runs,
    )

    summary = summarize(
        records
    )

    print()
    print("Summary")
    print("=" * 72)

    for row in summary:
        if row["successes"]:
            print(
                f"{row['provider']:8} "
                f"{row['mode']:10} "
                f"success={row['successes']}/"
                f"{row['runs']} "
                f"mean={row['mean_ms']:.1f} ms "
                f"median={row['median_ms']:.1f} ms "
                f"p95={row['p95_ms']:.1f} ms"
            )
        else:
            print(
                f"{row['provider']:8} "
                f"{row['mode']:10} "
                f"success=0/{row['runs']}"
            )

    if args.json_output:
        payload = {
            "records": [
                asdict(record)
                for record in records
            ],
            "summary": summary,
        }

        with open(
            args.json_output,
            "w",
            encoding="utf-8",
        ) as output_file:
            json.dump(
                payload,
                output_file,
                indent=2,
            )

        print()
        print(
            "Wrote benchmark JSON to "
            f"{args.json_output}"
        )


if __name__ == "__main__":
    main()