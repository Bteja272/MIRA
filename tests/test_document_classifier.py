import unittest

from app.services.document_classifier import (
    DocumentClassifier,
)


class DocumentClassifierTests(
    unittest.TestCase
):
    def test_classifies_alphanumeric_lab_report_from_content(
        self,
    ):
        text = """
SYNTHETIC MEDICAL RECORD

LABORATORY RESULTS

Hemoglobin A1c
Result: 7.2 %
Reference Range: 4.0 - 5.6 %
Flag: High

Glucose
Result: 138 mg/dL
Reference Range: 70 - 99 mg/dL
Flag: High
""".strip()

        result = (
            DocumentClassifier.classify(
                text=text,
                filename="7f2a9c81.pdf",
            )
        )

        self.assertEqual(
            result,
            "lab_report",
        )

    def test_classifies_alphanumeric_discharge_summary_from_content(
        self,
    ):
        text = """
DISCHARGE SUMMARY

Discharge Date: April 4, 2026

DISCHARGE DIAGNOSES
1. Type 2 diabetes mellitus
2. Hypertension

MEDICATIONS LISTED AT DISCHARGE
Metformin 500 mg twice daily.

FOLLOW-UP INSTRUCTIONS
Schedule a follow-up appointment.
""".strip()

        result = (
            DocumentClassifier.classify(
                text=text,
                filename="91ab2c77.txt",
            )
        )

        self.assertEqual(
            result,
            "discharge_summary",
        )

    def test_filename_alone_cannot_classify_document(
        self,
    ):
        text = """
This document contains general administrative information
without medical test results, diagnoses, prescriptions,
insurance claims, or clinical notes.
""".strip()

        result = (
            DocumentClassifier.classify(
                text=text,
                filename="lab_report.pdf",
            )
        )

        self.assertEqual(
            result,
            "unknown",
        )

    def test_content_overrides_misleading_filename(
        self,
    ):
        text = """
DISCHARGE SUMMARY

Date of Discharge: April 4, 2026
Discharge Diagnoses:
1. Hypertension

Condition at Discharge: Stable

Follow-up instructions:
Schedule an appointment within two weeks.
""".strip()

        result = (
            DocumentClassifier.classify(
                text=text,
                filename="laboratory_results.pdf",
            )
        )

        self.assertEqual(
            result,
            "discharge_summary",
        )

    def test_returns_unknown_for_insufficient_content(
        self,
    ):
        result = (
            DocumentClassifier.classify(
                text=(
                    "Patient document generated "
                    "on March 12, 2026."
                ),
                filename="a8bd77c1.pdf",
            )
        )

        self.assertEqual(
            result,
            "unknown",
        )

    def test_classifies_visit_note_from_supporting_content(
        self,
    ):
        text = """
Chief Complaint:
Routine follow-up.

Physical Examination:
Vital signs reviewed.

Assessment:
Symptoms are documented.

Plan:
Return for follow-up.
""".strip()

        result = (
            DocumentClassifier.classify(
                text=text,
                filename="document.txt",
            )
        )

        self.assertEqual(
            result,
            "visit_note",
        )

    def test_classifies_imaging_report(
        self,
    ):
        text = """
RADIOLOGY REPORT

Technique:
CT scan performed without contrast.

Findings:
No acute abnormality.

Impression:
No acute radiographic finding.
""".strip()

        result = (
            DocumentClassifier.classify(
                text=text,
                filename="3d0a12bc.pdf",
            )
        )

        self.assertEqual(
            result,
            "imaging_report",
        )

    def test_empty_text_returns_unknown(
        self,
    ):
        result = (
            DocumentClassifier.classify(
                text="",
                filename="lab_report.pdf",
            )
        )

        self.assertEqual(
            result,
            "unknown",
        )


if __name__ == "__main__":
    unittest.main()