from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from evaluation.models import RAGEvalCase


@dataclass(frozen=True)
class GenerationCaseResult:
    case_id: str
    task: str
    required_fact_recall: float
    missing_required_facts: tuple[str, ...]
    forbidden_fact_violation: bool
    forbidden_facts_found: tuple[str, ...]
    abstention_correct: bool
    case_passed: bool


class GenerationEvaluator:
    ABSTENTION_PATTERNS = (
        re.compile(
            r"\bnot documented\b",
            re.IGNORECASE,
        ),
        
        re.compile(
            r"\bdoes not include any information\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bno\b.{0,80}\bis documented\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bno information "
            r"(?:is )?documented\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bthere is no "
            r"information documented\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bdoes not document\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bdoesn't document\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bnot reported\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bno reference to\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bnot present\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bnot provided\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bnot available\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bcannot determine\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bcan't determine\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bdoes not contain\b",
            re.IGNORECASE,
        ),
    )

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        normalized = (
            value or ""
        )

        normalized = normalized.replace(
            "\u202f",
            " ",
        )
        normalized = normalized.replace(
            "\u00a0",
            " ",
        )

        return re.sub(
            r"\s+",
            " ",
            normalized
            .strip()
            .casefold(),
        )

    @classmethod
    def _contains_fact(
        cls,
        *,
        answer: str,
        fact: str,
    ) -> bool:
        normalized_answer = (
            cls._normalize(
                answer
            )
        )
        normalized_fact = (
            cls._normalize(
                fact
            )
        )

        return bool(
            normalized_fact
            and normalized_fact
            in normalized_answer
        )

    @classmethod
    def _contains_unnegated_forbidden_fact(
        cls,
        *,
        answer: str,
        fact: str,
    ) -> bool:
        """
        Count a forbidden literal only when it appears as an
        affirmative occurrence.

        This intentionally handles only narrow, deterministic
        negation immediately before the matched phrase. It does not
        attempt general semantic inference.
        """
        normalized_answer = (
            cls._normalize(
                answer
            )
        )
        normalized_fact = (
            cls._normalize(
                fact
            )
        )

        if not normalized_fact:
            return False

        start = 0

        while True:
            index = normalized_answer.find(
                normalized_fact,
                start,
            )

            if index < 0:
                return False

            prefix = normalized_answer[
                max(
                    0,
                    index - 16,
                ):
                index
            ]

            negated = bool(
                re.search(
                    r"(?:^|\s)"
                    r"(?:no|not|never|without)"
                    r"\s+$",
                    prefix,
                    flags=re.IGNORECASE,
                )
            )

            if not negated:
                return True

            start = (
                index
                + len(
                    normalized_fact
                )
            )

    @classmethod
    def _is_abstention(
        cls,
        answer: str,
    ) -> bool:
        return any(
            pattern.search(
                answer or ""
            )
            is not None
            for pattern
            in cls.ABSTENTION_PATTERNS
        )

    @classmethod
    def evaluate(
        cls,
        *,
        case: RAGEvalCase,
        answer: str,
        grounded_is_valid: bool,
    ) -> GenerationCaseResult:
        missing_required = tuple(
            fact
            for fact
            in case.required_facts
            if not cls._contains_fact(
                answer=answer,
                fact=fact,
            )
        )

        required_fact_recall = (
            (
                len(case.required_facts)
                - len(missing_required)
            )
            / len(case.required_facts)
            if case.required_facts
            else 1.0
        )

        forbidden_found = tuple(
            fact
            for fact
            in case.forbidden_facts
            if cls
            ._contains_unnegated_forbidden_fact(
                answer=answer,
                fact=fact,
            )
        )

        forbidden_violation = bool(
            forbidden_found
        )

        observed_abstention = (
            cls._is_abstention(
                answer
            )
        )

        abstention_correct = (
            observed_abstention
            if case.expected_abstention
            else not observed_abstention
        )

        case_passed = (
            required_fact_recall == 1.0
            and not forbidden_violation
            and abstention_correct
            and grounded_is_valid
        )

        return GenerationCaseResult(
            case_id=case.case_id,
            task=case.task,
            required_fact_recall=(
                required_fact_recall
            ),
            missing_required_facts=(
                missing_required
            ),
            forbidden_fact_violation=(
                forbidden_violation
            ),
            forbidden_facts_found=(
                forbidden_found
            ),
            abstention_correct=(
                abstention_correct
            ),
            case_passed=(
                case_passed
            ),
        )


def aggregate_generation_results(
    results: list[
        GenerationCaseResult
    ],
) -> dict[str, Any]:
    if not results:
        return {
            "case_count": 0,
            "required_fact_recall": 0.0,
            "forbidden_fact_violation_rate": 0.0,
            "abstention_accuracy": 0.0,
            "case_pass_rate": 0.0,
        }

    count = len(
        results
    )

    return {
        "case_count": count,
        "required_fact_recall": (
            sum(
                result.required_fact_recall
                for result in results
            )
            / count
        ),
        "forbidden_fact_violation_rate": (
            sum(
                1.0
                if result.forbidden_fact_violation
                else 0.0
                for result in results
            )
            / count
        ),
        "abstention_accuracy": (
            sum(
                1.0
                if result.abstention_correct
                else 0.0
                for result in results
            )
            / count
        ),
        "case_pass_rate": (
            sum(
                1.0
                if result.case_passed
                else 0.0
                for result in results
            )
            / count
        ),
    }
