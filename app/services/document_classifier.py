from pathlib import Path


class DocumentClassifier:
    SUPPORTED_TYPES = {
        "lab_report",
        "discharge_summary",
        "prescription",
        "imaging_report",
        "pathology_report",
        "visit_note",
        "vaccination_record",
        "insurance_document",
        "unknown",
    }

    STRONG_MARKERS = {
        "discharge_summary": (
            "discharge summary",
            "discharge diagnosis",
            "discharge instructions",
            "date of discharge",
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
        ),
        "imaging_report": (
            "radiology report",
            "imaging report",
            "radiologic findings",
            "impression:",
            "technique:",
        ),
        "pathology_report": (
            "pathology report",
            "surgical pathology",
            "histopathology",
            "microscopic description",
        ),
        "visit_note": (
            "progress note",
            "clinical note",
            "visit note",
            "history of present illness",
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
        ),
    }

    SUPPORTING_MARKERS = {
        "lab_report": (
            "hemoglobin",
            "glucose",
            "cholesterol",
            "result:",
            "flag:",
            "mg/dl",
        ),
        "discharge_summary": (
            "admission date",
            "follow-up",
            "discharge medication",
            "hospital course",
            "condition at discharge",
        ),
        "prescription": (
            "dosage",
            "take one",
            "tablet",
            "capsule",
            "refill",
        ),
        "imaging_report": (
            "mri",
            "ct scan",
            "x-ray",
            "ultrasound",
            "findings",
        ),
        "pathology_report": (
            "specimen",
            "diagnosis",
            "gross description",
            "biopsy",
            "malignant",
        ),
        "visit_note": (
            "chief complaint",
            "assessment",
            "plan",
            "physical examination",
            "vital signs",
        ),
        "vaccination_record": (
            "vaccine",
            "dose",
            "manufacturer",
            "lot number",
            "administered",
        ),
        "insurance_document": (
            "claim number",
            "deductible",
            "copay",
            "provider charge",
            "patient responsibility",
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
            "progress_note",
            "clinical_note",
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

    @classmethod
    def classify(
        cls,
        text: str,
        filename: str | None = None,
    ) -> str:
        normalized_text = (text or "").lower()
        normalized_filename = (
            Path(filename).stem.lower()
            if filename
            else ""
        )

        scores = {
            document_type: 0
            for document_type in cls.STRONG_MARKERS
        }

        for document_type, markers in (
            cls.STRONG_MARKERS.items()
        ):
            for marker in markers:
                if marker in normalized_text:
                    scores[document_type] += 4

        for document_type, markers in (
            cls.SUPPORTING_MARKERS.items()
        ):
            for marker in markers:
                if marker in normalized_text:
                    scores[document_type] += 1

        for document_type, markers in (
            cls.FILENAME_MARKERS.items()
        ):
            for marker in markers:
                if marker in normalized_filename:
                    scores[document_type] += 3

        best_type = max(
            scores,
            key=scores.get,
        )

        if scores[best_type] < 3:
            return "unknown"

        return best_type