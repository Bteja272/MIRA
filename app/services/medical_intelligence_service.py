import hashlib
import re
from datetime import (UTC, date, datetime)

from app.schemas.extraction_persistence import (
    PersistedMedicalExtraction,
)
from app.schemas.intelligence_api import (
    IntelligenceCompareResponse,
    IntelligenceTimelineResponse,
)
from app.schemas.medical_extraction import (
    MedicalDocumentExtraction,
    SourceEvidence,
)
from app.schemas.medical_intelligence import (
    ChangeType,
    IntelligenceStatus,
    MedicalDocumentIntelligence,
    MedicalEntityType,
    MedicalRecordChange,
    MedicalTimelineEvent,
    NormalizationMethod,
    NormalizedMedicalEntity,
    TimelineEventType,
)
from app.services.medical_extraction_persistence_service import (
    MedicalExtractionPersistenceService,
)
from app.services.medical_extraction_service import (
    MedicalExtractionService,
)
from app.services.medical_intelligence_guidance_service import (
    MedicalIntelligenceGuidanceService,
)


class MedicalIntelligenceError(
    RuntimeError
):
    pass


class MedicalIntelligenceExtractionError(
    MedicalIntelligenceError
):
    pass


class MedicalIntelligenceService:
    """
    Deterministic intelligence derived from a validated
    structured extraction.

    The service reports documentary changes only. It does
    not infer that a condition resolved, medication stopped,
    laboratory result improved/worsened, or treatment
    succeeded merely because selected records differ.
    """

    LAB_ALIASES = {
        "hgb": "hemoglobin",
        "hb": "hemoglobin",
        "wbc": (
            "white blood cell count"
        ),
        "rbc": (
            "red blood cell count"
        ),
        "plt": "platelet count",
    }

    @staticmethod
    def _clean_name(
        value: str,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            value.strip(),
        )

    @classmethod
    def _canonical_text(
        cls,
        value: str,
    ) -> str:
        cleaned = (
            cls._clean_name(
                value
            )
            .casefold()
        )

        cleaned = re.sub(
            r"[^a-z0-9]+",
            " ",
            cleaned,
        )

        return re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()

    @classmethod
    def _normalize_name(
        cls,
        entity_type: MedicalEntityType,
        raw_name: str,
    ) -> tuple[
        str,
        NormalizationMethod,
    ]:
        cleaned = cls._clean_name(
            raw_name
        )

        canonical = cls._canonical_text(
            cleaned
        )

        if (
            entity_type
            == MedicalEntityType.LAB
            and canonical
            in cls.LAB_ALIASES
        ):
            return (
                cls.LAB_ALIASES[
                    canonical
                ],
                NormalizationMethod.ALIAS,
            )

        return (
            cleaned,
            NormalizationMethod.EXACT,
        )

    @classmethod
    def _canonical_key(
        cls,
        entity_type: MedicalEntityType,
        normalized_name: str,
    ) -> str:
        return (
            f"{entity_type.value}:"
            f"{cls._canonical_text(normalized_name)}"
        )

    @classmethod
    def normalize_entities(
        cls,
        extraction: (
            MedicalDocumentExtraction
        ),
    ) -> list[
        NormalizedMedicalEntity
    ]:
        entities: list[
            NormalizedMedicalEntity
        ] = []

        for diagnosis in (
            extraction.diagnoses
        ):
            (
                normalized_name,
                method,
            ) = cls._normalize_name(
                MedicalEntityType.DIAGNOSIS,
                diagnosis.name,
            )

            if diagnosis.code:
                method = (
                    NormalizationMethod
                    .DOCUMENTED_CODE
                )

            entities.append(
                NormalizedMedicalEntity(
                    entity_type=(
                        MedicalEntityType
                        .DIAGNOSIS
                    ),
                    raw_name=diagnosis.name,
                    normalized_name=(
                        normalized_name
                    ),
                    canonical_key=(
                        cls._canonical_key(
                            MedicalEntityType
                            .DIAGNOSIS,
                            normalized_name,
                        )
                    ),
                    code=diagnosis.code,
                    code_system=(
                        diagnosis.code_system
                    ),
                    status=(
                        diagnosis.status.value
                    ),
                    confidence=(
                        diagnosis.confidence
                    ),
                    normalization_method=(
                        method
                    ),
                    details={},
                    sources=(
                        diagnosis.sources
                    ),
                )
            )

        for medication in (
            extraction.medications
        ):
            (
                normalized_name,
                method,
            ) = cls._normalize_name(
                MedicalEntityType.MEDICATION,
                medication.name,
            )

            entities.append(
                NormalizedMedicalEntity(
                    entity_type=(
                        MedicalEntityType
                        .MEDICATION
                    ),
                    raw_name=medication.name,
                    normalized_name=(
                        normalized_name
                    ),
                    canonical_key=(
                        cls._canonical_key(
                            MedicalEntityType
                            .MEDICATION,
                            normalized_name,
                        )
                    ),
                    status=(
                        medication.status.value
                    ),
                    confidence=(
                        medication.confidence
                    ),
                    normalization_method=(
                        method
                    ),
                    details={
                        "dose": medication.dose,
                        "route": (
                            medication.route
                        ),
                        "frequency": (
                            medication.frequency
                        ),
                        "duration": (
                            medication.duration
                        ),
                        "instructions": (
                            medication.instructions
                        ),
                    },
                    sources=(
                        medication.sources
                    ),
                )
            )

        for lab in (
            extraction.lab_results
        ):
            (
                normalized_name,
                method,
            ) = cls._normalize_name(
                MedicalEntityType.LAB,
                lab.test_name,
            )

            entities.append(
                NormalizedMedicalEntity(
                    entity_type=(
                        MedicalEntityType.LAB
                    ),
                    raw_name=lab.test_name,
                    normalized_name=(
                        normalized_name
                    ),
                    canonical_key=(
                        cls._canonical_key(
                            MedicalEntityType.LAB,
                            normalized_name,
                        )
                    ),
                    status=lab.flag.value,
                    confidence=(
                        lab.confidence
                    ),
                    normalization_method=(
                        method
                    ),
                    details={
                        "raw_value": (
                            lab.raw_value
                        ),
                        "numeric_value": (
                            lab.numeric_value
                        ),
                        "unit": lab.unit,
                        "reference_range": (
                            lab.reference_range
                        ),
                        "flag": (
                            lab.flag.value
                        ),
                        "collected_at": (
                            lab.collected_at
                            .normalized_value
                            if lab.collected_at
                            else None
                        ),
                    },
                    sources=(
                        lab.sources
                    ),
                )
            )

        for procedure in (
            extraction.procedures
        ):
            (
                normalized_name,
                method,
            ) = cls._normalize_name(
                MedicalEntityType.PROCEDURE,
                procedure.name,
            )

            entities.append(
                NormalizedMedicalEntity(
                    entity_type=(
                        MedicalEntityType
                        .PROCEDURE
                    ),
                    raw_name=procedure.name,
                    normalized_name=(
                        normalized_name
                    ),
                    canonical_key=(
                        cls._canonical_key(
                            MedicalEntityType
                            .PROCEDURE,
                            normalized_name,
                        )
                    ),
                    confidence=(
                        procedure.confidence
                    ),
                    normalization_method=(
                        method
                    ),
                    details={
                        "result": (
                            procedure.result
                        ),
                        "procedure_date": (
                            procedure
                            .procedure_date
                            .normalized_value
                            if (
                                procedure
                                .procedure_date
                            )
                            else None
                        ),
                    },
                    sources=(
                        procedure.sources
                    ),
                )
            )

        for provider in (
            extraction.providers
        ):
            (
                normalized_name,
                method,
            ) = cls._normalize_name(
                MedicalEntityType.PROVIDER,
                provider.name,
            )

            entities.append(
                NormalizedMedicalEntity(
                    entity_type=(
                        MedicalEntityType
                        .PROVIDER
                    ),
                    raw_name=provider.name,
                    normalized_name=(
                        normalized_name
                    ),
                    canonical_key=(
                        cls._canonical_key(
                            MedicalEntityType
                            .PROVIDER,
                            normalized_name,
                        )
                    ),
                    confidence=(
                        provider.confidence
                    ),
                    normalization_method=(
                        method
                    ),
                    details={
                        "role": provider.role,
                        "organization": (
                            provider.organization
                        ),
                    },
                    sources=(
                        provider.sources
                    ),
                )
            )

        return entities

    @staticmethod
    def _date_to_string(
        value: (
            date
            | datetime
            | str
            | None
        ),
        ) -> str | None:
            """
            Convert normalized extraction dates into the
            string representation used by intelligence
            responses and deterministic event identifiers.
            """

            if value is None:
                return None

            if isinstance(
                value,
                datetime,
            ):
                return value.isoformat()

            if isinstance(
                value,
                date,
            ):
                return value.isoformat()

            cleaned = str(
                value
            ).strip()

            return cleaned or None

    @staticmethod
    def _event_id(
        *parts: object,
    ) -> str:
        """
        Generate a deterministic identifier while
        safely handling dates and other scalar values.
        """

        payload = "|".join(
            (
                ""
                if part is None
                else str(part)
            )
            for part in parts
        )

        digest = hashlib.sha256(
            payload.encode(
                "utf-8"
            )
        ).hexdigest()

        return digest[:24]

    @classmethod
    def _document_date(
        cls,
        extraction: (
            MedicalDocumentExtraction
        ),
    ) -> str | None:
        if (
            extraction.document_date
            is None
        ):
            return None

        return cls._date_to_string(
            extraction
            .document_date
            .normalized_value
        )

    @classmethod
    def build_timeline(
        cls,
        extraction: (
            MedicalDocumentExtraction
        ),
    ) -> list[
        MedicalTimelineEvent
    ]:
        events: list[
            MedicalTimelineEvent
        ] = []

        document_date = (
            cls._document_date(
                extraction
            )
        )

        for diagnosis in (
            extraction.diagnoses
        ):
            detail = (
                "Documented diagnosis status: "
                f"{diagnosis.status.value}."
            )

            events.append(
                MedicalTimelineEvent(
                    event_id=cls._event_id(
                        extraction.document_id,
                        "diagnosis",
                        diagnosis.name,
                        document_date or "",
                    ),
                    document_id=(
                        extraction.document_id
                    ),
                    event_type=(
                        TimelineEventType
                        .DIAGNOSIS
                    ),
                    title=diagnosis.name,
                    detail=detail,
                    event_date=(
                        document_date
                    ),
                    sources=(
                        diagnosis.sources
                    ),
                )
            )

        for medication in (
            extraction.medications
        ):
            details: list[str] = [
                (
                    "Documented medication "
                    f"status: "
                    f"{medication.status.value}."
                )
            ]

            if medication.dose:
                details.append(
                    "Documented dose: "
                    f"{medication.dose}."
                )

            if medication.frequency:
                details.append(
                    "Documented frequency: "
                    f"{medication.frequency}."
                )

            events.append(
                MedicalTimelineEvent(
                    event_id=cls._event_id(
                        extraction.document_id,
                        "medication",
                        medication.name,
                        document_date or "",
                    ),
                    document_id=(
                        extraction.document_id
                    ),
                    event_type=(
                        TimelineEventType
                        .MEDICATION
                    ),
                    title=medication.name,
                    detail=" ".join(
                        details
                    ),
                    event_date=(
                        document_date
                    ),
                    sources=(
                        medication.sources
                    ),
                )
            )

        for lab in (
            extraction.lab_results
        ):
            event_date = (
                cls._date_to_string(
                    lab.collected_at
                    .normalized_value
                )
                if (
                    lab.collected_at
                    and lab.collected_at
                    .normalized_value
                )
                else document_date
            )

            result_text = (
                lab.raw_value
            )

            if lab.unit:
                result_text = (
                    f"{result_text} "
                    f"{lab.unit}"
                )

            events.append(
                MedicalTimelineEvent(
                    event_id=cls._event_id(
                        extraction.document_id,
                        "lab",
                        lab.test_name,
                        event_date or "",
                        result_text,
                    ),
                    document_id=(
                        extraction.document_id
                    ),
                    event_type=(
                        TimelineEventType.LAB
                    ),
                    title=lab.test_name,
                    detail=(
                        "Documented result: "
                        f"{result_text}. "
                        "Documented flag: "
                        f"{lab.flag.value}."
                    ),
                    event_date=event_date,
                    sources=(
                        lab.sources
                    ),
                )
            )

        for procedure in (
            extraction.procedures
        ):
            event_date = (
                cls._date_to_string(
                    procedure
                    .procedure_date
                    .normalized_value
                )
                if (
                    procedure
                    .procedure_date
                    and procedure
                    .procedure_date
                    .normalized_value
                )
                else document_date
            )

            events.append(
                MedicalTimelineEvent(
                    event_id=cls._event_id(
                        extraction.document_id,
                        "procedure",
                        procedure.name,
                        event_date or "",
                    ),
                    document_id=(
                        extraction.document_id
                    ),
                    event_type=(
                        TimelineEventType
                        .PROCEDURE
                    ),
                    title=procedure.name,
                    detail=(
                        procedure.result
                    ),
                    event_date=event_date,
                    sources=(
                        procedure.sources
                    ),
                )
            )

        for index, follow_up in enumerate(
            extraction
            .follow_up_instructions
        ):
            events.append(
                MedicalTimelineEvent(
                    event_id=cls._event_id(
                        extraction.document_id,
                        "follow_up",
                        str(index),
                        follow_up.instruction,
                    ),
                    document_id=(
                        extraction.document_id
                    ),
                    event_type=(
                        TimelineEventType
                        .FOLLOW_UP
                    ),
                    title="Follow-up",
                    detail=(
                        follow_up.instruction
                    ),
                    event_date=(
                        document_date
                    ),
                    sources=(
                        follow_up.sources
                    ),
                )
            )

        return sorted(
            events,
            key=lambda event: (
                event.event_date is None,
                event.event_date or "",
                event.event_type.value,
                event.title.casefold(),
            ),
        )

    @classmethod
    def build(
        cls,
        persisted_extraction: (
            PersistedMedicalExtraction
        ),
    ) -> MedicalDocumentIntelligence:
        extraction = (
            persisted_extraction.extraction
        )

        entities = (
            cls.normalize_entities(
                extraction
            )
        )

        guidance = (
            MedicalIntelligenceGuidanceService
            .build_cards(
                extraction
            )
        )

        timeline = cls.build_timeline(
            extraction
        )

        warnings: list[str] = []

        if not entities:
            warnings.append(
                "No supported medical entities were "
                "available for normalization."
            )

        if not guidance:
            warnings.append(
                "No documented diagnosis or supported "
                "injury topic produced an educational "
                "guidance card."
            )

        status = (
            IntelligenceStatus.COMPLETED
            if entities or timeline
            else IntelligenceStatus.PARTIAL
        )

        return MedicalDocumentIntelligence(
            document_id=(
                persisted_extraction
                .document_id
            ),
            source_extraction_id=(
                persisted_extraction
                .extraction_id
            ),
            source_extraction_updated_at=(
                persisted_extraction
                .updated_at
            ),
            status=status,
            normalized_entities=(
                entities
            ),
            guidance_cards=guidance,
            timeline_events=timeline,
            warnings=warnings,
            generated_at=datetime.now(UTC),
        )

    @classmethod
    def get_or_generate_extraction(
        cls,
        document_id: str,
        user_id: str,
    ) -> tuple[
        PersistedMedicalExtraction,
        bool,
    ]:
        existing = (
            MedicalExtractionPersistenceService
            .get(
                document_id=document_id,
                user_id=user_id,
            )
        )

        if existing is not None:
            return existing, False

        try:
            extraction = (
                MedicalExtractionService
                .extract(
                    document_id=document_id,
                    user_id=user_id,
                )
            )

            persisted = (
                MedicalExtractionPersistenceService
                .save(
                    extraction=extraction,
                    user_id=user_id,
                )
            )

            return persisted, True

        except Exception as exc:
            raise (
                MedicalIntelligenceExtractionError(
                    "A structured extraction could "
                    "not be prepared for medical "
                    "intelligence."
                )
            ) from exc

    @staticmethod
    def _summary(
        entity: (
            NormalizedMedicalEntity
        ),
    ) -> str:
        parts = [
            entity.normalized_name,
        ]

        if entity.status:
            parts.append(
                f"status={entity.status}"
            )

        for key in (
            "raw_value",
            "dose",
            "frequency",
            "unit",
        ):
            value = entity.details.get(
                key
            )

            if value is not None:
                parts.append(
                    f"{key}={value}"
                )

        return "; ".join(parts)

    @staticmethod
    def _merge_sources(
        *groups: list[
            SourceEvidence
        ],
    ) -> list[
        SourceEvidence
    ]:
        result: list[
            SourceEvidence
        ] = []

        seen: set[
            tuple[str, str, int, str]
        ] = set()

        for group in groups:
            for source in group:
                key = (
                    source.document_id,
                    source.chunk_id,
                    source.chunk_index,
                    source.quoted_text,
                )

                if key in seen:
                    continue

                seen.add(key)
                result.append(source)

        return result

    @staticmethod
    def _meaningful_details(
        entity: (
            NormalizedMedicalEntity
        ),
    ) -> dict:
        if (
            entity.entity_type
            == MedicalEntityType.LAB
        ):
            return {
                "raw_value": (
                    entity.details.get(
                        "raw_value"
                    )
                ),
                "numeric_value": (
                    entity.details.get(
                        "numeric_value"
                    )
                ),
                "unit": (
                    entity.details.get(
                        "unit"
                    )
                ),
                "flag": (
                    entity.details.get(
                        "flag"
                    )
                ),
            }

        if (
            entity.entity_type
            == MedicalEntityType.MEDICATION
        ):
            return {
                "dose": (
                    entity.details.get(
                        "dose"
                    )
                ),
                "route": (
                    entity.details.get(
                        "route"
                    )
                ),
                "frequency": (
                    entity.details.get(
                        "frequency"
                    )
                ),
                "duration": (
                    entity.details.get(
                        "duration"
                    )
                ),
            }

        return {}

    @classmethod
    def _compare_pair(
        cls,
        before: (
            MedicalDocumentIntelligence
        ),
        after: (
            MedicalDocumentIntelligence
        ),
    ) -> list[
        MedicalRecordChange
    ]:
        before_map = {
            entity.canonical_key: entity
            for entity
            in before.normalized_entities
            if entity.entity_type
            in {
                MedicalEntityType.DIAGNOSIS,
                MedicalEntityType.MEDICATION,
                MedicalEntityType.LAB,
                MedicalEntityType.PROCEDURE,
            }
        }

        after_map = {
            entity.canonical_key: entity
            for entity
            in after.normalized_entities
            if entity.entity_type
            in {
                MedicalEntityType.DIAGNOSIS,
                MedicalEntityType.MEDICATION,
                MedicalEntityType.LAB,
                MedicalEntityType.PROCEDURE,
            }
        }

        changes: list[
            MedicalRecordChange
        ] = []

        for key in sorted(
            after_map.keys()
            - before_map.keys()
        ):
            entity = after_map[key]

            changes.append(
                MedicalRecordChange(
                    entity_type=(
                        entity.entity_type
                    ),
                    canonical_key=key,
                    normalized_name=(
                        entity.normalized_name
                    ),
                    change_type=(
                        ChangeType.APPEARED
                    ),
                    from_document_id=(
                        before.document_id
                    ),
                    to_document_id=(
                        after.document_id
                    ),
                    description=(
                        "This item appears in the "
                        "later selected record but "
                        "was not found in the earlier "
                        "selected record."
                    ),
                    before_summary=None,
                    after_summary=(
                        cls._summary(entity)
                    ),
                    sources=entity.sources,
                )
            )

        for key in sorted(
            before_map.keys()
            - after_map.keys()
        ):
            entity = before_map[key]

            changes.append(
                MedicalRecordChange(
                    entity_type=(
                        entity.entity_type
                    ),
                    canonical_key=key,
                    normalized_name=(
                        entity.normalized_name
                    ),
                    change_type=(
                        ChangeType
                        .NOT_MENTIONED_LATER
                    ),
                    from_document_id=(
                        before.document_id
                    ),
                    to_document_id=(
                        after.document_id
                    ),
                    description=(
                        "This item was found in the "
                        "earlier selected record but "
                        "was not found in the later "
                        "selected record. This does "
                        "not establish that the "
                        "condition resolved or that "
                        "a medication was stopped."
                    ),
                    before_summary=(
                        cls._summary(entity)
                    ),
                    after_summary=None,
                    sources=entity.sources,
                )
            )

        for key in sorted(
            before_map.keys()
            & after_map.keys()
        ):
            old = before_map[key]
            new = after_map[key]

            if (
                old.status
                != new.status
                and (
                    old.status is not None
                    or new.status is not None
                )
            ):
                changes.append(
                    MedicalRecordChange(
                        entity_type=(
                            new.entity_type
                        ),
                        canonical_key=key,
                        normalized_name=(
                            new.normalized_name
                        ),
                        change_type=(
                            ChangeType
                            .STATUS_CHANGED
                        ),
                        from_document_id=(
                            before.document_id
                        ),
                        to_document_id=(
                            after.document_id
                        ),
                        description=(
                            "The documented status "
                            "differs between the two "
                            "selected records. MIRA "
                            "does not interpret whether "
                            "this represents clinical "
                            "improvement or worsening."
                        ),
                        before_summary=(
                            cls._summary(old)
                        ),
                        after_summary=(
                            cls._summary(new)
                        ),
                        sources=(
                            cls._merge_sources(
                                old.sources,
                                new.sources,
                            )
                        ),
                    )
                )

            old_details = (
                cls._meaningful_details(
                    old
                )
            )

            new_details = (
                cls._meaningful_details(
                    new
                )
            )

            if (
                old_details
                and new_details
                and old_details
                != new_details
            ):
                changes.append(
                    MedicalRecordChange(
                        entity_type=(
                            new.entity_type
                        ),
                        canonical_key=key,
                        normalized_name=(
                            new.normalized_name
                        ),
                        change_type=(
                            ChangeType
                            .VALUE_CHANGED
                        ),
                        from_document_id=(
                            before.document_id
                        ),
                        to_document_id=(
                            after.document_id
                        ),
                        description=(
                            "The documented value or "
                            "details differ between "
                            "the selected records. "
                            "MIRA reports the change "
                            "without determining its "
                            "clinical significance."
                        ),
                        before_summary=(
                            cls._summary(old)
                        ),
                        after_summary=(
                            cls._summary(new)
                        ),
                        sources=(
                            cls._merge_sources(
                                old.sources,
                                new.sources,
                            )
                        ),
                    )
                )

        return changes

    @classmethod
    def _load_intelligence_inputs(
        cls,
        document_ids: list[str],
        user_id: str,
    ) -> list[
        tuple[
            PersistedMedicalExtraction,
            MedicalDocumentIntelligence,
        ]
    ]:
        records: list[
            tuple[
                PersistedMedicalExtraction,
                MedicalDocumentIntelligence,
            ]
        ] = []

        for document_id in document_ids:
            extraction, _ = (
                cls
                .get_or_generate_extraction(
                    document_id=(
                        document_id
                    ),
                    user_id=user_id,
                )
            )

            records.append(
                (
                    extraction,
                    cls.build(
                        extraction
                    ),
                )
            )

        def sort_key(
            item: tuple[
                PersistedMedicalExtraction,
                MedicalDocumentIntelligence,
            ],
        ) -> tuple[str, str]:
            extraction = item[0]

            normalized_date = None

            if (
                extraction
                .extraction
                .document_date
            ):
                normalized_date = (
                    cls._date_to_string(
                        extraction
                        .extraction
                        .document_date
                        .normalized_value
                    )
                )

            return (
                normalized_date
                or extraction
                .created_at
                .isoformat(),
                extraction.document_id,
            )

        return sorted(
            records,
            key=sort_key,
        )

    @classmethod
    def timeline(
        cls,
        document_ids: list[str],
        user_id: str,
    ) -> IntelligenceTimelineResponse:
        records = (
            cls._load_intelligence_inputs(
                document_ids=document_ids,
                user_id=user_id,
            )
        )

        events = [
            event
            for _, intelligence
            in records
            for event
            in intelligence.timeline_events
        ]

        events.sort(
            key=lambda event: (
                event.event_date is None,
                event.event_date or "",
                event.document_id,
                event.event_type.value,
            )
        )

        ordered_ids = [
            extraction.document_id
            for extraction, _
            in records
        ]

        return (
            IntelligenceTimelineResponse(
                document_ids=ordered_ids,
                events=events,
                notices=[
                    (
                        "Timeline entries represent "
                        "documented events only. "
                        "Missing dates are not inferred."
                    ),
                    (
                        "Record order does not establish "
                        "cause, treatment response, or "
                        "clinical outcome."
                    ),
                ],
                generated_at=datetime.now(UTC),
            )
        )

    @classmethod
    def compare(
        cls,
        document_ids: list[str],
        user_id: str,
    ) -> IntelligenceCompareResponse:
        records = (
            cls._load_intelligence_inputs(
                document_ids=document_ids,
                user_id=user_id,
            )
        )

        changes: list[
            MedicalRecordChange
        ] = []

        for index in range(
            len(records) - 1
        ):
            before = records[index][1]
            after = records[
                index + 1
            ][1]

            changes.extend(
                cls._compare_pair(
                    before,
                    after,
                )
            )

        ordered_ids = [
            extraction.document_id
            for extraction, _
            in records
        ]

        return (
            IntelligenceCompareResponse(
                document_ids=ordered_ids,
                changes=changes,
                notices=[
                    (
                        "A finding that is absent from "
                        "a later selected document is "
                        "reported only as not mentioned "
                        "later. It is not treated as "
                        "resolved or discontinued."
                    ),
                    (
                        "Changes in laboratory values, "
                        "medication details, or statuses "
                        "are reported without judging "
                        "whether they are clinically "
                        "better, worse, appropriate, "
                        "or causal."
                    ),
                ],
                generated_at=(
                    datetime.now(UTC)
                ),
            )
        )