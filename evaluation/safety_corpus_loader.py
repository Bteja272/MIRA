from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SafetyCase:
    case_id: str
    query: str
    expected_allowed: bool
    expected_category: str


@dataclass(frozen=True)
class RoutingCase:
    case_id: str
    query: str
    document_ids: list[str]
    expected_route: str


@dataclass(frozen=True)
class SafetyCorpus:
    version: str
    safety_cases: list[SafetyCase]
    routing_cases: list[RoutingCase]

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> "SafetyCorpus":
        payload = json.loads(
            Path(path).read_text(
                encoding="utf-8"
            )
        )

        safety_cases = [
            SafetyCase(**item)
            for item
            in payload["safety_cases"]
        ]
        routing_cases = [
            RoutingCase(**item)
            for item
            in payload["routing_cases"]
        ]

        safety_ids = [
            item.case_id
            for item in safety_cases
        ]
        route_ids = [
            item.case_id
            for item in routing_cases
        ]

        if len(safety_ids) != len(set(safety_ids)):
            raise ValueError(
                "Duplicate safety case_id."
            )

        if len(route_ids) != len(set(route_ids)):
            raise ValueError(
                "Duplicate routing case_id."
            )

        allowed_categories = {
            "allowed",
            "emergency",
            "self_harm",
            "diagnosis",
            "prognosis",
            "medication_change",
        }

        for case in safety_cases:
            if (
                case.expected_category
                not in allowed_categories
            ):
                raise ValueError(
                    "Unsupported safety category: "
                    f"{case.expected_category}"
                )

            if (
                case.expected_allowed
                and case.expected_category
                != "allowed"
            ):
                raise ValueError(
                    "Allowed safety cases must use "
                    "expected_category='allowed'."
                )

            if (
                not case.expected_allowed
                and case.expected_category
                == "allowed"
            ):
                raise ValueError(
                    "Blocked safety cases cannot use "
                    "expected_category='allowed'."
                )

        for case in routing_cases:
            if case.expected_route not in {
                "direct",
                "web",
                "rag",
            }:
                raise ValueError(
                    "Unsupported route: "
                    f"{case.expected_route}"
                )

        return cls(
            version=str(
                payload.get(
                    "version",
                    "unknown",
                )
            ),
            safety_cases=safety_cases,
            routing_cases=routing_cases,
        )