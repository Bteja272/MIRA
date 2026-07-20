import unittest

from app.services.document_classifier import (
    DocumentClassifier,
)


class DocumentClassifierTests(
    unittest.TestCase
):
    def test_classifies_lab_report(self):
        text = """
        LABORATORY RESULTS

        Hemoglobin A1c
        Result: 7.2 %
        Reference Range: 4.0 - 5.6 %
        Flag: High
        """

        result = DocumentClassifier.classify(
            text=text,
            filename="synthetic_lab_report.txt",
        )

        self.assertEqual(
            result,
            "lab_report",
        )

    def test_classifies_discharge_summary(self):
        text = """
        DISCHARGE SUMMARY

        Admission Date: March 10, 2026
        Date of Discharge: March 12, 2026
        Discharge Diagnosis: Hypertension
        Discharge Instructions: Follow up in one week.
        """

        result = DocumentClassifier.classify(
            text=text,
            filename=(
                "synthetic_discharge_summary.txt"
            ),
        )

        self.assertEqual(
            result,
            "discharge_summary",
        )

    def test_classifies_imaging_report(self):
        text = """
        RADIOLOGY REPORT

        Technique: CT scan without contrast.
        Findings: No acute abnormality.
        Impression: No acute findings.
        """

        result = DocumentClassifier.classify(
            text=text,
            filename="radiology_report.txt",
        )

        self.assertEqual(
            result,
            "imaging_report",
        )

    def test_unknown_document(self):
        text = """
        This is an ordinary document without recognizable
        medical document structure.
        """

        result = DocumentClassifier.classify(
            text=text,
            filename="notes.txt",
        )

        self.assertEqual(
            result,
            "unknown",
        )

    def test_every_result_is_supported(self):
        result = DocumentClassifier.classify(
            text="Prescription with two refills remaining.",
            filename="prescription.txt",
        )

        self.assertIn(
            result,
            DocumentClassifier.SUPPORTED_TYPES,
        )


if __name__ == "__main__":
    unittest.main()