import logging

from app.services.medical_extraction_service import (
    MedicalExtractionService,
)


def test_safe_error_type_excludes_exception_message():
    sensitive_value = (
        "Synthetic Patient has fracture "
        "and takes SyntheticMed 10 mg"
    )

    exc = RuntimeError(
        sensitive_value
    )

    result = (
        MedicalExtractionService
        ._safe_error_type(
            exc
        )
    )

    assert result == "RuntimeError"
    assert sensitive_value not in result


def test_safe_error_type_does_not_expose_str_exception():
    exc = ValueError(
        "Synthetic MRN 123456"
    )

    safe_value = (
        MedicalExtractionService
        ._safe_error_type(
            exc
        )
    )

    assert safe_value == "ValueError"
    assert "123456" not in safe_value
    assert "Synthetic" not in safe_value