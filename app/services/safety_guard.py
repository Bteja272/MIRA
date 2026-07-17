import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    category: str
    response: str | None = None


class SafetyGuard:
    """
    Deterministic pre-routing medical safety check.

    This runs before the LangGraph LLM classifier so unsafe requests
    never reach document retrieval, web search, or model generation.
    """

    DOCUMENT_TERMS = (
        "document",
        "report",
        "uploaded",
        "medical record",
        "medical records",
        "discharge summary",
        "lab report",
        "prescription",
        "according to",
        "the file",
        "my records",
    )

    SELF_HARM_PATTERNS = (
        r"\bkill myself\b",
        r"\bhurt myself\b",
        r"\bend my life\b",
        r"\bwant to die\b",
        r"\bi am suicidal\b",
        r"\bi'm suicidal\b",
    )

    EMERGENCY_PATTERNS = (
        (
            r"\b(i am|i'm|im|currently|right now|"
            r"i feel|i have|i'm having|i am having)"
            r".{0,60}"
            r"\b(chest pain|cannot breathe|can't breathe|"
            r"difficulty breathing|shortness of breath|"
            r"bleeding heavily|severe bleeding|"
            r"overdose|overdosed|unconscious)\b"
        ),
        r"\b(can't breathe|cannot breathe|struggling to breathe)\b",
        r"\b(i overdosed|i have overdosed|i took too many pills)\b",
        r"\b(bleeding heavily|severe uncontrolled bleeding)\b",
        r"\b(someone is unconscious|i am unconscious)\b",
    )

    MEDICATION_PATTERNS = (
        (
            r"\bshould i "
            r"(start|stop|increase|decrease|change|skip|double|replace)"
            r"\b"
        ),
        r"\bcan i (start|stop|combine|mix)\b",
        (
            r"\b(change|increase|decrease|double|skip|adjust)"
            r" (my )?(dose|dosage|medication|medicine)\b"
        ),
        r"\bshould i take more\b",
        r"\bshould i take less\b",
    )

    PROGNOSIS_PATTERNS = (
        r"\bwill i be (okay|fine|alright)\b",
        r"\bhow long do i have\b",
        r"\bwill (this|it) kill me\b",
        r"\bwhat are my chances\b",
        r"\bwill i recover\b",
        r"\blife expectancy\b",
    )

    THIRD_PARTY_PATTERNS = (
        (
            r"\b(my friend|my coworker|my neighbor|my partner|"
            r"my husband|my wife|my brother|my sister|someone i know)"
            r".{0,80}"
            r"\b(do they have|what do they have|diagnose|"
            r"what is wrong|should they take)\b"
        ),
    )

    DIAGNOSIS_PATTERNS = (
        r"\bdo i have\b",
        r"\bcould i have\b",
        r"\bmight i have\b",
        r"\bwhat do i have\b",
        r"\bwhat is wrong with me\b",
        r"\bdiagnose me\b",
        r"\bwhat condition do i have\b",
        r"\bare these symptoms (of|from)\b",
    )

    RESPONSES = {
        "self_harm": (
            "MIRA cannot safely handle this situation. If you may be in "
            "immediate danger, contact your local emergency services now "
            "and reach out to a crisis service or trusted person nearby. "
            "Do not wait for an online response."
        ),
        "emergency": (
            "If you may be experiencing a medical emergency, call your "
            "local emergency services now or go to the nearest emergency "
            "department. Do not wait for MIRA or another online response."
        ),
        "diagnosis_request": (
            "MIRA cannot diagnose a condition from symptoms described in "
            "the conversation. It can explain diagnoses and findings that "
            "are explicitly documented in your uploaded medical records. "
            "Please contact a healthcare professional about current symptoms."
        ),
        "medication_request": (
            "MIRA cannot recommend starting, stopping, replacing, or "
            "changing the dose of a medication. It can explain medication "
            "instructions already documented in your uploaded records. "
            "Please contact your prescriber or pharmacist for medication decisions."
        ),
        "prognosis_request": (
            "MIRA cannot predict medical outcomes or provide a prognosis. "
            "It can explain what your uploaded records document. Please "
            "discuss outcome-related questions with your treating clinician."
        ),
        "third_party_request": (
            "MIRA is designed to explain the user's own uploaded medical "
            "records. It cannot diagnose or recommend treatment for another person."
        ),
    }

    @staticmethod
    def _normalize(query: str) -> str:
        normalized = query.lower().replace("’", "'")
        return re.sub(r"\s+", " ", normalized).strip()

    @staticmethod
    def _matches(query: str, patterns: tuple[str, ...]) -> bool:
        return any(
            re.search(pattern, query, flags=re.IGNORECASE)
            for pattern in patterns
        )

    @classmethod
    def _references_document(cls, query: str) -> bool:
        return any(term in query for term in cls.DOCUMENT_TERMS)

    @classmethod
    def evaluate(cls, query: str) -> SafetyDecision:
        normalized = cls._normalize(query)

        if not normalized:
            return SafetyDecision(
                allowed=False,
                category="invalid_query",
                response="Please provide a question.",
            )

        if cls._matches(normalized, cls.SELF_HARM_PATTERNS):
            return SafetyDecision(
                allowed=False,
                category="self_harm",
                response=cls.RESPONSES["self_harm"],
            )

        if cls._matches(normalized, cls.EMERGENCY_PATTERNS):
            return SafetyDecision(
                allowed=False,
                category="emergency",
                response=cls.RESPONSES["emergency"],
            )

        if cls._matches(normalized, cls.MEDICATION_PATTERNS):
            return SafetyDecision(
                allowed=False,
                category="medication_request",
                response=cls.RESPONSES["medication_request"],
            )

        if cls._matches(normalized, cls.PROGNOSIS_PATTERNS):
            return SafetyDecision(
                allowed=False,
                category="prognosis_request",
                response=cls.RESPONSES["prognosis_request"],
            )

        if cls._matches(normalized, cls.THIRD_PARTY_PATTERNS):
            return SafetyDecision(
                allowed=False,
                category="third_party_request",
                response=cls.RESPONSES["third_party_request"],
            )

        # A documented diagnosis may be explained. An undocumented
        # symptom-based diagnosis request must be blocked.
        if (
            cls._matches(normalized, cls.DIAGNOSIS_PATTERNS)
            and not cls._references_document(normalized)
        ):
            return SafetyDecision(
                allowed=False,
                category="diagnosis_request",
                response=cls.RESPONSES["diagnosis_request"],
            )

        return SafetyDecision(
            allowed=True,
            category="allowed",
        )