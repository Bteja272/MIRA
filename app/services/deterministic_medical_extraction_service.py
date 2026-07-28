import re
from datetime import (
    date,
    datetime,
)
from typing import Any

from app.schemas.medical_extraction import (
    ExtractionMethod,
    ExtractionStatus,
    LabResultFlag,
    LabResultInformation,
    MedicalDocumentExtraction,
    MedicalDocumentType,
    MedicationInformation,
    MedicationStatus,
    PatientInformation,
    SourceEvidence,
    SourcedDateValue,
    SourcedTextValue,
)


class DeterministicMedicalExtractionService:
    """
    Extract high-confidence medical facts without using an LLM.

    This service intentionally supports conservative patterns only.
    It must leave uncertain information unextracted rather than guess.
    """

    PATIENT_NAME_PATTERN = re.compile(
        r"^\s*(?:patient(?:\s+name)?|patient's name)"
        r"\s*[:\-]\s*(?P<value>.+?)\s*$",
        re.IGNORECASE,
    )

    DATE_OF_BIRTH_PATTERN = re.compile(
        r"^\s*(?:date\s+of\s+birth|dob)"
        r"\s*[:\-]\s*(?P<value>.+?)\s*$",
        re.IGNORECASE,
    )

    DOCUMENT_DATE_PATTERN = re.compile(
        r"^\s*(?:report\s+date|document\s+date|"
        r"date\s+of\s+service|service\s+date)"
        r"\s*[:\-]\s*(?P<value>.+?)\s*$",
        re.IGNORECASE,
    )

    LAB_VALUE_PATTERN = re.compile(
        r"^(?P<value>"
        r"(?:[<>]=?\s*)?-?\d+(?:\.\d+)?"
        r"|positive"
        r"|negative"
        r"|reactive"
        r"|non[\s\-]?reactive"
        r"|detected"
        r"|not\s+detected"
        r")\b",
        re.IGNORECASE,
    )

    REFERENCE_RANGE_PATTERN = re.compile(
        r"(?:reference\s*range|ref(?:erence)?\s*range|"
        r"normal\s*range|range)"
        r"\s*[:\-]?\s*"
        r"(?P<range>"
        r"[<>]?\s*-?\d+(?:\.\d+)?"
        r"\s*(?:-|–|—|to)\s*"
        r"[<>]?\s*-?\d+(?:\.\d+)?"
        r")",
        re.IGNORECASE,
    )

    PARENTHETICAL_RANGE_PATTERN = re.compile(
        r"[\(\[]\s*"
        r"(?P<range>"
        r"[<>]?\s*-?\d+(?:\.\d+)?"
        r"\s*(?:-|–|—|to)\s*"
        r"[<>]?\s*-?\d+(?:\.\d+)?"
        r")"
        r"\s*[\)\]]",
        re.IGNORECASE,
    )

    LAB_FLAG_PATTERN = re.compile(
        r"\b(?P<flag>"
        r"high|low|normal|abnormal|critical|"
        r"positive|negative|H|L"
        r")\b",
        re.IGNORECASE,
    )

    MEDICATION_SECTION_PATTERN = re.compile(
        r"^\s*(?:"
        r"medications?"
        r"|current\s+medications?"
        r"|discharge\s+medications?"
        r")\s*:?\s*$",
        re.IGNORECASE,
    )

    MEDICATION_INLINE_PATTERN = re.compile(
        r"^\s*(?:"
        r"medication"
        r"|current\s+medication"
        r"|discharge\s+medication"
        r")\s*[:\-]\s*(?P<body>.+?)\s*$",
        re.IGNORECASE,
    )

    MEDICATION_DOSE_PATTERN = re.compile(
        r"\b(?P<dose>"
        r"\d+(?:\.\d+)?\s*"
        r"(?:mg|mcg|g|kg|ml|mL|units?|IU)"
        r")\b",
        re.IGNORECASE,
    )

    LAB_NAME_KEYWORDS = {
        "albumin",
        "alkaline phosphatase",
        "alt",
        "antibody",
        "antigen",
        "ast",
        "bilirubin",
        "blood urea nitrogen",
        "bun",
        "calcium",
        "chloride",
        "cholesterol",
        "creatinine",
        "crp",
        "d dimer",
        "ferritin",
        "glucose",
        "hba1c",
        "hematocrit",
        "hemoglobin",
        "iron",
        "ldl",
        "hdl",
        "magnesium",
        "phosphorus",
        "platelet",
        "potassium",
        "protein",
        "rbc",
        "red blood cell",
        "sodium",
        "t3",
        "t4",
        "triglycerides",
        "troponin",
        "tsh",
        "vitamin",
        "wbc",
        "white blood cell",
    }

    NON_LAB_LABELS = {
        "age",
        "account number",
        "address",
        "date",
        "date of birth",
        "dob",
        "fax",
        "medical record number",
        "mrn",
        "patient id",
        "phone",
        "report date",
        "room number",
        "service date",
    }

    DATE_FORMATS = (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
    )

    FREQUENCY_PATTERNS = (
        (
            re.compile(
                r"\bonce\s+daily\b",
                re.IGNORECASE,
            ),
            "once daily",
        ),
        (
            re.compile(
                r"\btwice\s+daily\b",
                re.IGNORECASE,
            ),
            "twice daily",
        ),
        (
            re.compile(
                r"\bthree\s+times\s+daily\b",
                re.IGNORECASE,
            ),
            "three times daily",
        ),
        (
            re.compile(
                r"\bevery\s+\d+\s+hours?\b",
                re.IGNORECASE,
            ),
            None,
        ),
        (
            re.compile(
                r"\bas\s+needed\b|\bprn\b",
                re.IGNORECASE,
            ),
            "as needed",
        ),
        (
            re.compile(
                r"\bdaily\b|\bqd\b",
                re.IGNORECASE,
            ),
            "daily",
        ),
        (
            re.compile(
                r"\bbid\b",
                re.IGNORECASE,
            ),
            "twice daily",
        ),
        (
            re.compile(
                r"\btid\b",
                re.IGNORECASE,
            ),
            "three times daily",
        ),
        (
            re.compile(
                r"\bnightly\b|\bqhs\b",
                re.IGNORECASE,
            ),
            "nightly",
        ),
    )

    ROUTE_PATTERNS = (
        (
            re.compile(
                r"\bby\s+mouth\b|\boral(?:ly)?\b|\bpo\b",
                re.IGNORECASE,
            ),
            "oral",
        ),
        (
            re.compile(
                r"\bintravenous(?:ly)?\b|\biv\b",
                re.IGNORECASE,
            ),
            "intravenous",
        ),
        (
            re.compile(
                r"\bintramuscular(?:ly)?\b|\bim\b",
                re.IGNORECASE,
            ),
            "intramuscular",
        ),
        (
            re.compile(
                r"\bsubcutaneous(?:ly)?\b|\bsubq\b",
                re.IGNORECASE,
            ),
            "subcutaneous",
        ),
        (
            re.compile(
                r"\btopical(?:ly)?\b",
                re.IGNORECASE,
            ),
            "topical",
        ),
        (
            re.compile(
                r"\binhaled\b|\binhalation\b",
                re.IGNORECASE,
            ),
            "inhaled",
        ),
    )

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:
        return " ".join(
            value.casefold().split()
        )

    @classmethod
    def _normalize_document_type(
        cls,
        value: str | None,
    ) -> MedicalDocumentType:
        try:
            return MedicalDocumentType(
                value or "unknown"
            )

        except ValueError:
            return (
                MedicalDocumentType.UNKNOWN
            )

    @classmethod
    def _parse_date(
        cls,
        raw_value: str,
    ) -> date | None:
        cleaned = raw_value.strip().rstrip(
            ".,;"
        )

        for date_format in cls.DATE_FORMATS:
            try:
                return datetime.strptime(
                    cleaned,
                    date_format,
                ).date()

            except ValueError:
                continue

        return None

    @staticmethod
    def _build_source(
        document: dict[str, Any],
        chunk: dict[str, Any],
        quoted_text: str,
    ) -> SourceEvidence:
        return SourceEvidence(
            document_id=str(
                document["document_id"]
            ),
            chunk_id=str(
                chunk["chunk_id"]
            ),
            source_filename=(
                document.get("filename")
            ),
            page_number=(
                chunk.get("page_number")
            ),
            chunk_index=int(
                chunk["chunk_index"]
            ),
            quoted_text=(
                quoted_text.strip()
            ),
        )

    @classmethod
    def _extract_patient_information(
        cls,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> tuple[
        PatientInformation,
        SourcedDateValue | None,
    ]:
        patient_name = None
        date_of_birth = None
        document_date = None

        for chunk in chunks:
            for line in str(
                chunk.get("text") or ""
            ).splitlines():
                cleaned_line = line.strip()

                if not cleaned_line:
                    continue

                if patient_name is None:
                    match = (
                        cls.PATIENT_NAME_PATTERN
                        .match(cleaned_line)
                    )

                    if match:
                        value = match.group(
                            "value"
                        ).strip()

                        if value:
                            patient_name = (
                                SourcedTextValue(
                                    value=value,
                                    confidence=0.99,
                                    extraction_method=(
                                        ExtractionMethod
                                        .DETERMINISTIC
                                    ),
                                    sources=[
                                        cls._build_source(
                                            document,
                                            chunk,
                                            cleaned_line,
                                        )
                                    ],
                                )
                            )

                if date_of_birth is None:
                    match = (
                        cls.DATE_OF_BIRTH_PATTERN
                        .match(cleaned_line)
                    )

                    if match:
                        raw_value = (
                            match.group(
                                "value"
                            ).strip()
                        )

                        if raw_value:
                            date_of_birth = (
                                SourcedDateValue(
                                    raw_value=raw_value,
                                    normalized_value=(
                                        cls._parse_date(
                                            raw_value
                                        )
                                    ),
                                    confidence=0.97,
                                    extraction_method=(
                                        ExtractionMethod
                                        .DETERMINISTIC
                                    ),
                                    sources=[
                                        cls._build_source(
                                            document,
                                            chunk,
                                            cleaned_line,
                                        )
                                    ],
                                )
                            )

                if document_date is None:
                    match = (
                        cls.DOCUMENT_DATE_PATTERN
                        .match(cleaned_line)
                    )

                    if match:
                        raw_value = (
                            match.group(
                                "value"
                            ).strip()
                        )

                        if raw_value:
                            document_date = (
                                SourcedDateValue(
                                    raw_value=raw_value,
                                    normalized_value=(
                                        cls._parse_date(
                                            raw_value
                                        )
                                    ),
                                    confidence=0.95,
                                    extraction_method=(
                                        ExtractionMethod
                                        .DETERMINISTIC
                                    ),
                                    sources=[
                                        cls._build_source(
                                            document,
                                            chunk,
                                            cleaned_line,
                                        )
                                    ],
                                )
                            )

        patient = PatientInformation(
            name=patient_name,
            date_of_birth=date_of_birth,
        )

        return patient, document_date

    @classmethod
    def _map_lab_flag(
        cls,
        raw_flag: str | None,
        raw_value: str,
    ) -> LabResultFlag:
        normalized_value = (
            cls._normalize_text(
                raw_value
            )
        )

        if normalized_value == "positive":
            return LabResultFlag.POSITIVE

        if normalized_value == "negative":
            return LabResultFlag.NEGATIVE

        if not raw_flag:
            return LabResultFlag.UNKNOWN

        normalized_flag = (
            raw_flag.strip().casefold()
        )

        flag_map = {
            "h": LabResultFlag.HIGH,
            "high": LabResultFlag.HIGH,
            "l": LabResultFlag.LOW,
            "low": LabResultFlag.LOW,
            "normal": (
                LabResultFlag.NORMAL
            ),
            "abnormal": (
                LabResultFlag.ABNORMAL
            ),
            "critical": (
                LabResultFlag.CRITICAL
            ),
            "positive": (
                LabResultFlag.POSITIVE
            ),
            "negative": (
                LabResultFlag.NEGATIVE
            ),
        }

        return flag_map.get(
            normalized_flag,
            LabResultFlag.UNKNOWN,
        )

    @staticmethod
    def _numeric_value(
        raw_value: str,
    ) -> float | None:
        cleaned = re.sub(
            r"^[<>]=?\s*",
            "",
            raw_value.strip(),
        )

        try:
            return float(cleaned)

        except ValueError:
            return None

    @classmethod
    def _parse_lab_line(
        cls,
        document: dict[str, Any],
        chunk: dict[str, Any],
        line: str,
    ) -> LabResultInformation | None:
        if ":" not in line and "=" not in line:
            return None

        parts = re.split(
            r"\s*[:=]\s*",
            line,
            maxsplit=1,
        )

        if len(parts) != 2:
            return None

        test_name = parts[0].strip(
            " \t-*•"
        )

        result_text = parts[1].strip()

        if not test_name or not result_text:
            return None

        normalized_name = (
            cls._normalize_text(
                test_name
            )
        )

        if normalized_name in cls.NON_LAB_LABELS:
            return None

        value_match = (
            cls.LAB_VALUE_PATTERN
            .match(result_text)
        )

        if value_match is None:
            return None

        raw_value = (
            value_match.group(
                "value"
            ).strip()
        )

        remaining_text = (
            result_text[
                value_match.end():
            ]
            .strip()
        )

        range_match = (
            cls.REFERENCE_RANGE_PATTERN
            .search(remaining_text)
        )

        if range_match is None:
            range_match = (
                cls.PARENTHETICAL_RANGE_PATTERN
                .search(remaining_text)
            )

        reference_range = None

        if range_match is not None:
            reference_range = (
                range_match.group(
                    "range"
                ).strip()
            )

        flag_search_text = (
            remaining_text
        )

        if range_match is not None:
            flag_search_text = (
                remaining_text[
                    :range_match.start()
                ]
                + " "
                + remaining_text[
                    range_match.end():
                ]
            )

        flag_match = (
            cls.LAB_FLAG_PATTERN
            .search(flag_search_text)
        )

        raw_flag = (
            flag_match.group("flag")
            if flag_match
            else None
        )

        cut_positions: list[int] = []

        if range_match is not None:
            cut_positions.append(
                range_match.start()
            )

        if flag_match is not None:
            cut_positions.append(
                flag_match.start()
            )

        unit_end = (
            min(cut_positions)
            if cut_positions
            else len(remaining_text)
        )

        unit_candidate = (
            remaining_text[:unit_end]
            .strip(" \t,;()[]-")
        )

        unit = None

        if (
            unit_candidate
            and len(unit_candidate) <= 50
            and not re.search(
                r"\b(?:reference|range|high|low|"
                r"normal|abnormal|critical)\b",
                unit_candidate,
                re.IGNORECASE,
            )
        ):
            unit = unit_candidate

        has_known_lab_name = any(
            keyword in normalized_name
            for keyword
            in cls.LAB_NAME_KEYWORDS
        )

        has_structured_lab_evidence = any(
            (
                unit,
                reference_range,
                raw_flag,
                has_known_lab_name,
            )
        )

        if not has_structured_lab_evidence:
            return None

        return LabResultInformation(
            test_name=test_name,
            raw_value=raw_value,
            numeric_value=(
                cls._numeric_value(
                    raw_value
                )
            ),
            unit=unit,
            reference_range=(
                reference_range
            ),
            flag=cls._map_lab_flag(
                raw_flag=raw_flag,
                raw_value=raw_value,
            ),
            confidence=0.98,
            extraction_method=(
                ExtractionMethod
                .DETERMINISTIC
            ),
            sources=[
                cls._build_source(
                    document=document,
                    chunk=chunk,
                    quoted_text=line,
                )
            ],
        )

    @classmethod
    def _extract_lab_results(
        cls,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> list[LabResultInformation]:
        results: list[
            LabResultInformation
        ] = []

        seen_keys: set[
            tuple[str, str, str]
        ] = set()

        for chunk in chunks:
            for line in str(
                chunk.get("text") or ""
            ).splitlines():
                cleaned_line = line.strip()

                if not cleaned_line:
                    continue

                result = cls._parse_lab_line(
                    document=document,
                    chunk=chunk,
                    line=cleaned_line,
                )

                if result is None:
                    continue

                key = (
                    cls._normalize_text(
                        result.test_name
                    ),
                    cls._normalize_text(
                        result.raw_value
                    ),
                    cls._normalize_text(
                        result.unit or ""
                    ),
                )

                if key in seen_keys:
                    continue

                seen_keys.add(key)
                results.append(result)

        return results

    @classmethod
    def _extract_frequency(
        cls,
        body: str,
    ) -> str | None:
        for pattern, fixed_value in (
            cls.FREQUENCY_PATTERNS
        ):
            match = pattern.search(
                body
            )

            if match:
                return (
                    fixed_value
                    if fixed_value
                    else match.group(0)
                )

        return None

    @classmethod
    def _extract_route(
        cls,
        body: str,
    ) -> str | None:
        for pattern, route in (
            cls.ROUTE_PATTERNS
        ):
            if pattern.search(body):
                return route

        return None

    @classmethod
    def _parse_medication_body(
        cls,
        document: dict[str, Any],
        chunk: dict[str, Any],
        body: str,
        source_line: str,
    ) -> MedicationInformation | None:
        cleaned_body = body.strip(
            " \t-*•"
        )

        dose_match = (
            cls.MEDICATION_DOSE_PATTERN
            .search(cleaned_body)
        )

        # A dose is required for deterministic medication
        # extraction to avoid treating ordinary text as a drug.
        if dose_match is None:
            return None

        medication_name = (
            cleaned_body[
                :dose_match.start()
            ]
            .strip(" \t,;:-")
        )

        if not medication_name:
            return None

        status = MedicationStatus.CURRENT

        if re.search(
            r"\b(?:discontinued|stop|stopped)\b",
            cleaned_body,
            re.IGNORECASE,
        ):
            status = (
                MedicationStatus.DISCONTINUED
            )

        elif re.search(
            r"\bas\s+needed\b|\bprn\b",
            cleaned_body,
            re.IGNORECASE,
        ):
            status = (
                MedicationStatus.AS_NEEDED
            )

        return MedicationInformation(
            name=medication_name,
            dose=dose_match.group(
                "dose"
            ),
            route=cls._extract_route(
                cleaned_body
            ),
            frequency=(
                cls._extract_frequency(
                    cleaned_body
                )
            ),
            instructions=cleaned_body,
            status=status,
            confidence=0.94,
            extraction_method=(
                ExtractionMethod
                .DETERMINISTIC
            ),
            sources=[
                cls._build_source(
                    document=document,
                    chunk=chunk,
                    quoted_text=source_line,
                )
            ],
        )

    @classmethod
    def _extract_medications(
        cls,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> list[MedicationInformation]:
        medications: list[
            MedicationInformation
        ] = []

        seen_keys: set[
            tuple[str, str]
        ] = set()

        for chunk in chunks:
            inside_medication_section = (
                False
            )

            for line in str(
                chunk.get("text") or ""
            ).splitlines():
                cleaned_line = line.strip()

                if not cleaned_line:
                    inside_medication_section = (
                        False
                    )
                    continue

                if (
                    cls.MEDICATION_SECTION_PATTERN
                    .match(cleaned_line)
                ):
                    inside_medication_section = (
                        True
                    )
                    continue

                inline_match = (
                    cls.MEDICATION_INLINE_PATTERN
                    .match(cleaned_line)
                )

                if inline_match:
                    medication_body = (
                        inline_match.group(
                            "body"
                        )
                    )

                elif inside_medication_section:
                    # Stop when another heading begins.
                    if (
                        cleaned_line.endswith(":")
                        and not re.search(
                            r"\d",
                            cleaned_line,
                        )
                    ):
                        inside_medication_section = (
                            False
                        )
                        continue

                    medication_body = (
                        cleaned_line
                    )

                else:
                    continue

                medication = (
                    cls._parse_medication_body(
                        document=document,
                        chunk=chunk,
                        body=medication_body,
                        source_line=(
                            cleaned_line
                        ),
                    )
                )

                if medication is None:
                    continue

                key = (
                    cls._normalize_text(
                        medication.name
                    ),
                    cls._normalize_text(
                        medication.dose or ""
                    ),
                )

                if key in seen_keys:
                    continue

                seen_keys.add(key)
                medications.append(
                    medication
                )

        return medications

    @staticmethod
    def _calculate_confidence(
        patient: PatientInformation,
        document_date: (
            SourcedDateValue | None
        ),
        lab_results: list[
            LabResultInformation
        ],
        medications: list[
            MedicationInformation
        ],
    ) -> float:
        confidence_values: list[
            float
        ] = []

        for patient_value in (
            patient.name,
            patient.date_of_birth,
            patient.medical_record_number,
        ):
            if patient_value is not None:
                confidence_values.append(
                    patient_value.confidence
                )

        if document_date is not None:
            confidence_values.append(
                document_date.confidence
            )

        confidence_values.extend(
            result.confidence
            for result in lab_results
        )

        confidence_values.extend(
            medication.confidence
            for medication
            in medications
        )

        if not confidence_values:
            return 0.0

        return round(
            sum(confidence_values)
            / len(confidence_values),
            3,
        )

    @classmethod
    def extract(
        cls,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> MedicalDocumentExtraction:
        patient, document_date = (
            cls._extract_patient_information(
                document=document,
                chunks=chunks,
            )
        )

        lab_results = (
            cls._extract_lab_results(
                document=document,
                chunks=chunks,
            )
        )

        medications = (
            cls._extract_medications(
                document=document,
                chunks=chunks,
            )
        )

        confidence = (
            cls._calculate_confidence(
                patient=patient,
                document_date=(
                    document_date
                ),
                lab_results=lab_results,
                medications=medications,
            )
        )

        return MedicalDocumentExtraction(
            document_id=str(
                document["document_id"]
            ),
            document_type=(
                cls._normalize_document_type(
                    document.get(
                        "document_type"
                    )
                )
            ),
            status=(
                ExtractionStatus.PARTIAL
            ),
            patient=patient,
            document_date=document_date,
            lab_results=lab_results,
            medications=medications,
            extraction_confidence=(
                confidence
            ),
        )