from __future__ import annotations

from typing import Any


def _nullable_string() -> dict[str, Any]:
    return {
        "anyOf": [
            {"type": "string"},
            {"type": "null"},
        ]
    }


def _closed_object(
    properties: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
        "additionalProperties": False,
    }


MEDICAL_EXTRACTION_CANDIDATE_STRICT_SCHEMA: dict[
    str,
    Any,
] = _closed_object(
    {
        "patient": _closed_object(
            {
                "name": _nullable_string(),
                "date_of_birth": _nullable_string(),
                "medical_record_number": _nullable_string(),
            }
        ),
        "document_date": _nullable_string(),
        "providers": {
            "type": "array",
            "items": _closed_object(
                {
                    "name": {"type": "string"},
                    "role": _nullable_string(),
                    "organization": _nullable_string(),
                }
            ),
        },
        "diagnoses": {
            "type": "array",
            "items": _closed_object(
                {
                    "name": {"type": "string"},
                    "code": _nullable_string(),
                    "code_system": _nullable_string(),
                    "status": {
                        "type": "string",
                        "enum": [
                            "active",
                            "resolved",
                            "historical",
                            "ruled_out",
                            "unknown",
                        ],
                    },
                }
            ),
        },
        "medications": {
            "type": "array",
            "items": _closed_object(
                {
                    "name": {"type": "string"},
                    "dose": _nullable_string(),
                    "route": _nullable_string(),
                    "frequency": _nullable_string(),
                    "duration": _nullable_string(),
                    "instructions": _nullable_string(),
                    "status": {
                        "type": "string",
                        "enum": [
                            "current",
                            "historical",
                            "discontinued",
                            "as_needed",
                            "unknown",
                        ],
                    },
                }
            ),
        },
        "lab_results": {
            "type": "array",
            "items": _closed_object(
                {
                    "test_name": {"type": "string"},
                    "raw_value": {"type": "string"},
                    "unit": _nullable_string(),
                    "reference_range": _nullable_string(),
                    "flag": {
                        "type": "string",
                        "enum": [
                            "high",
                            "low",
                            "normal",
                            "abnormal",
                            "critical",
                            "positive",
                            "negative",
                            "unknown",
                        ],
                    },
                    "collected_at": _nullable_string(),
                }
            ),
        },
        "procedures": {
            "type": "array",
            "items": _closed_object(
                {
                    "name": {"type": "string"},
                    "procedure_date": _nullable_string(),
                    "result": _nullable_string(),
                }
            ),
        },
        "follow_up_instructions": {
            "type": "array",
            "items": _closed_object(
                {
                    "instruction": {"type": "string"},
                    "timeframe": _nullable_string(),
                    "specialty": _nullable_string(),
                }
            ),
        },
    }
)