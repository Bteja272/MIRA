from datetime import datetime

from app.schemas.extraction_persistence import (
    PersistedMedicalExtraction,
)
from app.schemas.medical_intelligence import (
    ChangeType,
    GuidanceLevel,
    MedicalEntityType,
)
from app.services.medical_intelligence_service import (
    MedicalIntelligenceService,
)


def _persisted_extraction(
    *,
    document_id: str,
    document_date: str,
    fracture: bool = True,
    medication_status: str = "current",
    lab_value: str = "12.0",
) -> PersistedMedicalExtraction:
    diagnoses = []

    if fracture:
        diagnoses.append(
            {
                "name": (
                    "Distal radius fracture"
                ),
                "code": None,
                "code_system": None,
                "status": "active",
                "confidence": 0.98,
                "extraction_method": (
                    "hybrid"
                ),
                "sources": [
                    {
                        "document_id": (
                            document_id
                        ),
                        "chunk_id": (
                            f"{document_id}-c1"
                        ),
                        "source_filename": (
                            "synthetic.txt"
                        ),
                        "page_number": 1,
                        "chunk_index": 0,
                        "quoted_text": (
                            "Distal radius fracture"
                        ),
                    }
                ],
            }
        )

    return (
        PersistedMedicalExtraction
        .model_validate(
            {
                "extraction_id": (
                    f"extract-{document_id}"
                ),
                "document_id": (
                    document_id
                ),
                "schema_version": "1.0",
                "status": "completed",
                "extraction_method": (
                    "hybrid"
                ),
                "model_name": (
                    "synthetic-test"
                ),
                "created_at": (
                    "2026-08-01T12:00:00"
                ),
                "updated_at": (
                    "2026-08-01T12:00:00"
                ),
                "extraction": {
                    "schema_version": "1.0",
                    "extraction_id": (
                        f"extract-{document_id}"
                    ),
                    "document_id": (
                        document_id
                    ),
                    "document_type": (
                        "discharge_summary"
                    ),
                    "status": "completed",
                    "patient": {
                        "name": None,
                        "date_of_birth": None,
                        (
                            "medical_record_number"
                        ): None,
                    },
                    "document_date": {
                        "raw_value": (
                            document_date
                        ),
                        "normalized_value": (
                            document_date
                        ),
                        "confidence": 1.0,
                        "extraction_method": (
                            "deterministic"
                        ),
                        "sources": [
                            {
                                "document_id": (
                                    document_id
                                ),
                                "chunk_id": (
                                    f"{document_id}-c1"
                                ),
                                "source_filename": (
                                    "synthetic.txt"
                                ),
                                "page_number": 1,
                                "chunk_index": 0,
                                "quoted_text": (
                                    document_date
                                ),
                            }
                        ],
                    },
                    "providers": [],
                    "diagnoses": diagnoses,
                    "medications": [
                        {
                            "name": (
                                "SyntheticMed"
                            ),
                            "dose": "10 mg",
                            "route": "oral",
                            "frequency": (
                                "once daily"
                            ),
                            "duration": None,
                            "instructions": None,
                            "status": (
                                medication_status
                            ),
                            "confidence": 0.95,
                            "extraction_method": (
                                "hybrid"
                            ),
                            "sources": [
                                {
                                    "document_id": (
                                        document_id
                                    ),
                                    "chunk_id": (
                                        f"{document_id}-c1"
                                    ),
                                    "source_filename": (
                                        "synthetic.txt"
                                    ),
                                    "page_number": 1,
                                    "chunk_index": 0,
                                    "quoted_text": (
                                        "SyntheticMed "
                                        "10 mg once daily"
                                    ),
                                }
                            ],
                        }
                    ],
                    "lab_results": [
                        {
                            "test_name": "Hgb",
                            "raw_value": (
                                lab_value
                            ),
                            "numeric_value": (
                                float(
                                    lab_value
                                )
                            ),
                            "unit": "g/dL",
                            "reference_range": (
                                "12-16 g/dL"
                            ),
                            "flag": "normal",
                            "collected_at": None,
                            "confidence": 0.96,
                            "extraction_method": (
                                "hybrid"
                            ),
                            "sources": [
                                {
                                    "document_id": (
                                        document_id
                                    ),
                                    "chunk_id": (
                                        f"{document_id}-c1"
                                    ),
                                    "source_filename": (
                                        "synthetic.txt"
                                    ),
                                    "page_number": 1,
                                    "chunk_index": 0,
                                    "quoted_text": (
                                        f"Hgb {lab_value} "
                                        "g/dL"
                                    ),
                                }
                            ],
                        }
                    ],
                    "procedures": [],
                    (
                        "follow_up_instructions"
                    ): [],
                    "warnings": [],
                    (
                        "extraction_confidence"
                    ): 0.96,
                    "generated_at": (
                        "2026-08-01T12:00:00"
                    ),
                },
            }
        )
    )


def test_normalizes_known_lab_alias():
    record = _persisted_extraction(
        document_id="doc-a",
        document_date="2026-08-01",
    )

    intelligence = (
        MedicalIntelligenceService
        .build(
            record
        )
    )

    labs = [
        entity
        for entity
        in intelligence
        .normalized_entities
        if (
            entity.entity_type
            == MedicalEntityType.LAB
        )
    ]

    assert len(labs) == 1

    assert (
        labs[0].normalized_name
        == "hemoglobin"
    )

    assert (
        labs[0].raw_name
        == "Hgb"
    )

    assert (
        labs[0].code
        is None
    )


def test_fracture_guidance_is_bounded():
    record = _persisted_extraction(
        document_id="doc-a",
        document_date="2026-08-01",
    )

    intelligence = (
        MedicalIntelligenceService
        .build(
            record
        )
    )

    fracture_cards = [
        card
        for card
        in intelligence.guidance_cards
        if "fracture"
        in card.topic.casefold()
    ]

    assert len(
        fracture_cards
    ) == 1

    card = fracture_cards[0]

    assert (
        card.guidance_level
        == GuidanceLevel.SUPPORTIVE
    )

    assert (
        "no_medication_changes"
        in card.safety_flags
    )

    assert (
        "no_medication_dosing"
        in card.safety_flags
    )

    assert card.red_flags

    combined = " ".join(
        card.supportive_care
    ).casefold()

    assert (
        "take 10 mg"
        not in combined
    )

    assert (
        "stop medication"
        not in combined
    )


def test_timeline_preserves_document_date():
    record = _persisted_extraction(
        document_id="doc-a",
        document_date="2026-08-01",
    )

    intelligence = (
        MedicalIntelligenceService
        .build(
            record
        )
    )

    assert (
        intelligence.timeline_events
    )

    assert all(
        event.document_id
        == "doc-a"
        for event
        in intelligence.timeline_events
    )


def test_comparison_uses_nonclinical_absence_language():
    first = (
        MedicalIntelligenceService
        .build(
            _persisted_extraction(
                document_id="doc-a",
                document_date=(
                    "2026-08-01"
                ),
                fracture=True,
            )
        )
    )

    second = (
        MedicalIntelligenceService
        .build(
            _persisted_extraction(
                document_id="doc-b",
                document_date=(
                    "2026-08-10"
                ),
                fracture=False,
            )
        )
    )

    changes = (
        MedicalIntelligenceService
        ._compare_pair(
            first,
            second,
        )
    )

    missing = [
        change
        for change
        in changes
        if (
            change.change_type
            == ChangeType
            .NOT_MENTIONED_LATER
        )
        and (
            "fracture"
            in change
            .normalized_name
            .casefold()
        )
    ]

    assert len(missing) == 1

    assert (
        "does not establish"
        in missing[0]
        .description
        .casefold()
    )


def test_lab_value_change_does_not_judge_clinical_direction():
    first = (
        MedicalIntelligenceService
        .build(
            _persisted_extraction(
                document_id="doc-a",
                document_date=(
                    "2026-08-01"
                ),
                lab_value="12.0",
            )
        )
    )

    second = (
        MedicalIntelligenceService
        .build(
            _persisted_extraction(
                document_id="doc-b",
                document_date=(
                    "2026-08-10"
                ),
                lab_value="13.0",
            )
        )
    )

    changes = (
        MedicalIntelligenceService
        ._compare_pair(
            first,
            second,
        )
    )

    lab_changes = [
        change
        for change
        in changes
        if (
            change.entity_type
            == MedicalEntityType.LAB
            and change.change_type
            == ChangeType.VALUE_CHANGED
        )
    ]

    assert lab_changes

    description = (
        lab_changes[0]
        .description
        .casefold()
    )

    assert (
        "without determining"
        in description
    )

    assert "improved" not in description
    assert "worsened" not in description