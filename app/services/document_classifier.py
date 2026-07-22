import re
from pathlib import Path


class DocumentClassifier:
    """
    Deterministic content-first medical-document classifier.

    Extracted document text is required for classification.
    Filename markers are used only as tie-breakers between document
    types that already have sufficient content evidence.
    """

    UNKNOWN_TYPE = "unknown"

    SUPPORTED_TYPES = {
        "lab_report",
        "discharge_summary",
        "prescription",
        "imaging_report",
        "pathology_report",
        "visit_note",
        "vaccination_record",
        "insurance_document",
        UNKNOWN_TYPE,
    }

    STRONG_MARKER_WEIGHT = 5
    SUPPORTING_MARKER_WEIGHT = 1
    MINIMUM_SUPPORTING_MATCHES = 3

    STRONG_MARKERS = {
        "discharge_summary": (
            "discharge summary",
            "discharge diagnosis",
            "discharge diagnoses",
            "discharge instructions",
            "date of discharge",
            "discharge date",
            "medications listed at discharge",
        ),
        "lab_report": (
            "laboratory results",
            "laboratory report",
            "reference range",
            "specimen collected",
        ),
        "prescription": (
            "prescription",
            "prescribed by",
            "rx number",
            "refills remaining",
            "prescriber information",
        ),
        "imaging_report": (
            "radiology report",
            "imaging report",
            "radiologic findings",
            "diagnostic imaging",
            "impression",
            "technique",
        ),
        "pathology_report": (
            "pathology report",
            "surgical pathology",
            "histopathology",
            "microscopic description",
            "final pathologic diagnosis",
        ),
        "visit_note": (
            "progress note",
            "clinical note",
            "visit note",
            "history of present illness",
            "office visit",
        ),
        "vaccination_record": (
            "vaccination record",
            "immunization record",
            "vaccine administered",
            "immunization history",
        ),
        "insurance_document": (
            "explanation of benefits",
            "insurance claim",
            "member id",
            "amount billed",
            "patient responsibility",
        ),
    }

    SUPPORTING_MARKERS = {
        "lab_report": (
            "hemoglobin",
            "glucose",
            "cholesterol",
            "result",
            "flag",
            "mg dl",
            "mmol l",
            "specimen",
        ),
        "discharge_summary": (
            "admission date",
            "follow up instructions",
            "follow up",
            "discharge medication",
            "hospital course",
            "condition at discharge",
            "attending physician",
        ),
        "prescription": (
            "dosage",
            "take one",
            "tablet",
            "capsule",
            "refill",
            "quantity",
            "pharmacy",
        ),
        "imaging_report": (
            "mri",
            "ct scan",
            "x ray",
            "xray",
            "ultrasound",
            "findings",
            "contrast",
        ),
        "pathology_report": (
            "specimen",
            "diagnosis",
            "gross description",
            "biopsy",
            "malignant",
            "benign",
        ),
        "visit_note": (
            "chief complaint",
            "assessment",
            "plan",
            "physical examination",
            "vital signs",
            "review of systems",
        ),
        "vaccination_record": (
            "vaccine",
            "dose",
            "manufacturer",
            "lot number",
            "administered",
            "administration site",
        ),
        "insurance_document": (
            "claim number",
            "deductible",
            "copay",
            "provider charge",
            "patient responsibility",
            "allowed amount",
        ),
    }

    FILENAME_MARKERS = {
        "lab_report": (
            "lab",
            "laboratory",
            "bloodwork",
        ),
        "discharge_summary": (
            "discharge",
        ),
        "prescription": (
            "prescription",
            "medication",
            "rx",
        ),
        "imaging_report": (
            "imaging",
            "radiology",
            "mri",
            "ct",
            "xray",
        ),
        "pathology_report": (
            "pathology",
            "biopsy",
        ),
        "visit_note": (
            "visit",
            "progress note",
            "clinical note",
        ),
        "vaccination_record": (
            "vaccination",
            "immunization",
            "vaccine",
        ),
        "insurance_document": (
            "insurance",
            "claim",
            "eob",
        ),
    }

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        normalized = value.lower()

        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            normalized,
        )

        return " ".join(
            normalized.split()
        )

    @classmethod
    def _contains_marker(
        cls,
        normalized_value: str,
        marker: str,
    ) -> bool:
        """
        Match complete words or phrases.

        This prevents `prescription` from matching `prescriptions`
        accidentally through ordinary substring matching.
        """
        normalized_marker = cls._normalize(
            marker
        )

        if (
            not normalized_value
            or not normalized_marker
        ):
            return False

        pattern = (
            rf"(?<![a-z0-9])"
            rf"{re.escape(normalized_marker)}"
            rf"(?![a-z0-9])"
        )

        return (
            re.search(
                pattern,
                normalized_value,
            )
            is not None
        )

    @classmethod
    def classify(
        cls,
        text: str,
        filename: str | None = None,
    ) -> str:
        normalized_text = cls._normalize(
            text or ""
        )

        # Filename alone must never classify a document.
        if not normalized_text:
            return cls.UNKNOWN_TYPE

        normalized_filename = cls._normalize(
            Path(filename).stem
            if filename
            else ""
        )

        evidence: dict[str, dict] = {}

        for document_type in cls.STRONG_MARKERS:
            strong_matches = [
                marker
                for marker
                in cls.STRONG_MARKERS[
                    document_type
                ]
                if cls._contains_marker(
                    normalized_text,
                    marker,
                )
            ]

            supporting_matches = [
                marker
                for marker
                in cls.SUPPORTING_MARKERS[
                    document_type
                ]
                if cls._contains_marker(
                    normalized_text,
                    marker,
                )
            ]

            filename_matches = [
                marker
                for marker
                in cls.FILENAME_MARKERS[
                    document_type
                ]
                if cls._contains_marker(
                    normalized_filename,
                    marker,
                )
            ]

            has_content_evidence = (
                bool(strong_matches)
                or len(supporting_matches)
                >= cls.MINIMUM_SUPPORTING_MATCHES
            )

            evidence[document_type] = {
                "has_content_evidence": (
                    has_content_evidence
                ),
                "content_score": (
                    len(strong_matches)
                    * cls.STRONG_MARKER_WEIGHT
                    + len(supporting_matches)
                    * cls.SUPPORTING_MARKER_WEIGHT
                ),
                "strong_match_count": (
                    len(strong_matches)
                ),
                "supporting_match_count": (
                    len(supporting_matches)
                ),
                "filename_hint": (
                    1
                    if filename_matches
                    else 0
                ),
            }

        eligible_types = [
            document_type
            for document_type, result
            in evidence.items()
            if result[
                "has_content_evidence"
            ]
        ]

        if not eligible_types:
            return cls.UNKNOWN_TYPE

        ranked_types = sorted(
            eligible_types,
            key=lambda document_type: (
                evidence[document_type][
                    "content_score"
                ],
                evidence[document_type][
                    "strong_match_count"
                ],
                evidence[document_type][
                    "supporting_match_count"
                ],
                evidence[document_type][
                    "filename_hint"
                ],
            ),
            reverse=True,
        )

        best_type = ranked_types[0]

        if len(ranked_types) > 1:
            best_rank = (
                evidence[best_type][
                    "content_score"
                ],
                evidence[best_type][
                    "strong_match_count"
                ],
                evidence[best_type][
                    "supporting_match_count"
                ],
                evidence[best_type][
                    "filename_hint"
                ],
            )

            second_type = ranked_types[1]

            second_rank = (
                evidence[second_type][
                    "content_score"
                ],
                evidence[second_type][
                    "strong_match_count"
                ],
                evidence[second_type][
                    "supporting_match_count"
                ],
                evidence[second_type][
                    "filename_hint"
                ],
            )

            if best_rank == second_rank:
                return cls.UNKNOWN_TYPE

        return best_type