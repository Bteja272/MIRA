import re
from dataclasses import dataclass

from app.schemas.medical_extraction import (
    MedicalDocumentExtraction,
    SourceEvidence,
)
from app.schemas.medical_intelligence import (
    DocumentedMedicalFact,
    GuidanceLevel,
    MedicalGuidanceCard,
)


@dataclass(frozen=True)
class GuidanceProfile:
    key: str
    patterns: tuple[str, ...]
    explanation: str
    general_information: tuple[str, ...]
    supportive_care: tuple[str, ...]
    red_flags: tuple[str, ...]
    when_to_seek_care: str
    questions: tuple[str, ...]


class MedicalIntelligenceGuidanceService:
    """
    Deterministic educational/supportive guidance.

    Guidance is produced only from conditions or procedures
    already documented in the structured extraction.

    This service does not:
    - diagnose from symptoms,
    - choose treatment,
    - recommend prescription medication,
    - provide dosing,
    - predict prognosis.
    """

    SAFETY_FLAGS = (
        "documented_condition_only",
        "no_diagnosis_inference",
        "no_medication_changes",
        "no_medication_dosing",
        "no_personalized_treatment",
        "no_prognosis",
    )

    PROFILES = (
        GuidanceProfile(
            key="fracture",
            patterns=(
                r"\bfracture\b",
                r"\bbroken bone\b",
            ),
            explanation=(
                "A fracture means that a bone has "
                "been cracked or broken. The exact "
                "location, pattern, stability, and "
                "treatment plan must come from the "
                "clinical record and treating team."
            ),
            general_information=(
                (
                    "Fracture care varies according "
                    "to the bone involved and the "
                    "specific injury pattern."
                ),
                (
                    "Follow-up may be used to check "
                    "healing, alignment, circulation, "
                    "sensation, and function."
                ),
            ),
            supportive_care=(
                (
                    "Protect the injured area and "
                    "follow any immobilization or "
                    "activity instructions already "
                    "given by the treating clinician."
                ),
                (
                    "Avoid placing unnecessary stress "
                    "on the injured area until the "
                    "treating team says the activity "
                    "is appropriate."
                ),
                (
                    "Keep scheduled follow-up and "
                    "imaging appointments."
                ),
            ),
            red_flags=(
                (
                    "New or worsening numbness, "
                    "tingling, or loss of sensation."
                ),
                (
                    "A limb or digits becoming pale, "
                    "blue, unusually cold, or difficult "
                    "to move."
                ),
                (
                    "Rapidly increasing swelling or "
                    "severe worsening pain."
                ),
                (
                    "An open wound over the injury, "
                    "visible bone, or uncontrolled "
                    "bleeding."
                ),
            ),
            when_to_seek_care=(
                "Seek urgent medical evaluation for "
                "new circulation or sensation changes, "
                "an open injury, uncontrolled bleeding, "
                "severe worsening symptoms, or another "
                "concern that may represent an emergency."
            ),
            questions=(
                (
                    "What activity or weight-bearing "
                    "restrictions apply to this injury?"
                ),
                (
                    "How long should the documented "
                    "support or immobilization plan "
                    "continue?"
                ),
                (
                    "When is follow-up imaging or "
                    "specialist review expected?"
                ),
            ),
        ),
        GuidanceProfile(
            key="sprain",
            patterns=(
                r"\bsprain\b",
                r"\bligament injury\b",
            ),
            explanation=(
                "A sprain is an injury involving a "
                "ligament, which connects bones around "
                "a joint. Severity can vary, so MIRA "
                "does not infer a grade from the name "
                "alone."
            ),
            general_information=(
                (
                    "A sprain can affect joint pain, "
                    "swelling, stability, and movement."
                ),
            ),
            supportive_care=(
                (
                    "Follow documented instructions "
                    "about support, movement, and "
                    "activity."
                ),
                (
                    "Avoid activities that clearly "
                    "worsen the injured joint until "
                    "the treating team advises otherwise."
                ),
            ),
            red_flags=(
                (
                    "New numbness, loss of sensation, "
                    "or marked weakness."
                ),
                (
                    "A limb or digits becoming pale, "
                    "blue, or unusually cold."
                ),
                (
                    "Major deformity or inability to "
                    "use the injured area after a "
                    "significant injury."
                ),
            ),
            when_to_seek_care=(
                "Seek prompt medical evaluation if "
                "symptoms are severe, rapidly worsening, "
                "or include circulation, sensation, or "
                "major functional changes."
            ),
            questions=(
                (
                    "Are there activity restrictions "
                    "for this injury?"
                ),
                (
                    "Is rehabilitation or physical "
                    "therapy recommended?"
                ),
            ),
        ),
        GuidanceProfile(
            key="strain",
            patterns=(
                r"\bstrain\b",
                r"\bmuscle injury\b",
                r"\btendon injury\b",
            ),
            explanation=(
                "A strain is an injury involving muscle "
                "or tendon tissue. MIRA does not infer "
                "the severity or healing time from the "
                "diagnosis name alone."
            ),
            general_information=(
                (
                    "Strains can affect pain, strength, "
                    "and movement depending on the "
                    "tissue involved."
                ),
            ),
            supportive_care=(
                (
                    "Follow the documented activity "
                    "and rehabilitation plan."
                ),
                (
                    "Avoid repeatedly stressing an area "
                    "when doing so clearly worsens the "
                    "documented injury."
                ),
            ),
            red_flags=(
                (
                    "Sudden major loss of strength or "
                    "function."
                ),
                (
                    "New numbness, major swelling, or "
                    "rapidly worsening symptoms."
                ),
            ),
            when_to_seek_care=(
                "Seek prompt medical evaluation for "
                "severe or rapidly worsening symptoms "
                "or major loss of function."
            ),
            questions=(
                (
                    "What activities should be limited "
                    "while this injury recovers?"
                ),
                (
                    "Is rehabilitation recommended?"
                ),
            ),
        ),
        GuidanceProfile(
            key="wound",
            patterns=(
                r"\blaceration\b",
                r"\bopen wound\b",
                r"\bwound\b",
                r"\bskin tear\b",
            ),
            explanation=(
                "A wound or laceration means that skin "
                "or underlying tissue has been injured. "
                "Depth, contamination, location, and "
                "other factors affect management."
            ),
            general_information=(
                (
                    "Wound care depends on the type "
                    "and location of the injury and on "
                    "instructions given during clinical "
                    "evaluation."
                ),
            ),
            supportive_care=(
                (
                    "Follow the wound-cleaning, dressing, "
                    "and activity instructions already "
                    "documented by the treating team."
                ),
                (
                    "Use clean hands when handling a "
                    "dressing or the area around the "
                    "wound."
                ),
                (
                    "Avoid applying unverified home "
                    "products to the wound."
                ),
            ),
            red_flags=(
                "Bleeding that will not stop.",
                (
                    "Rapidly increasing redness, "
                    "swelling, warmth, drainage, or "
                    "worsening pain."
                ),
                (
                    "New loss of sensation or function "
                    "near the injured area."
                ),
                (
                    "Fever or feeling significantly "
                    "unwell along with worsening wound "
                    "findings."
                ),
            ),
            when_to_seek_care=(
                "Seek urgent medical evaluation for "
                "uncontrolled bleeding, a deep or "
                "severe wound, loss of sensation or "
                "function, or rapidly worsening signs "
                "around the wound."
            ),
            questions=(
                (
                    "How should the dressing be managed "
                    "and when should it be changed?"
                ),
                (
                    "When should the wound be checked "
                    "again?"
                ),
                (
                    "What signs should prompt an earlier "
                    "review?"
                ),
            ),
        ),
        GuidanceProfile(
            key="burn",
            patterns=(
                r"\bburn\b",
            ),
            explanation=(
                "A burn is an injury to skin or deeper "
                "tissue. Severity depends on factors "
                "such as depth, size, location, and "
                "cause, which MIRA does not infer from "
                "the word 'burn' alone."
            ),
            general_information=(
                (
                    "Burn management varies substantially "
                    "with the extent and location of the "
                    "injury."
                ),
            ),
            supportive_care=(
                (
                    "Follow the dressing and wound-care "
                    "instructions documented by the "
                    "treating team."
                ),
                (
                    "Do not use unverified creams, oils, "
                    "or home remedies on the injured "
                    "area."
                ),
            ),
            red_flags=(
                (
                    "Difficulty breathing or a burn "
                    "involving the face or airway."
                ),
                (
                    "Large, deep, electrical, or chemical "
                    "burns."
                ),
                (
                    "Rapidly worsening swelling, pain, "
                    "redness, drainage, or systemic "
                    "illness."
                ),
            ),
            when_to_seek_care=(
                "Seek urgent medical evaluation for "
                "serious burns, breathing concerns, "
                "rapid worsening, or another possible "
                "emergency."
            ),
            questions=(
                (
                    "What wound-care instructions apply "
                    "to this burn?"
                ),
                (
                    "When should the area be reviewed "
                    "again?"
                ),
            ),
        ),
        GuidanceProfile(
            key="contusion",
            patterns=(
                r"\bcontusion\b",
                r"\bbruise\b",
            ),
            explanation=(
                "A contusion is a bruise caused by "
                "injury to soft tissue and small blood "
                "vessels without necessarily breaking "
                "the skin."
            ),
            general_information=(
                (
                    "The significance of a contusion "
                    "depends on its location, severity, "
                    "and associated injuries."
                ),
            ),
            supportive_care=(
                (
                    "Protect the injured area and follow "
                    "any documented activity guidance."
                ),
            ),
            red_flags=(
                (
                    "Rapidly increasing swelling or "
                    "severe worsening pain."
                ),
                (
                    "New weakness, numbness, or major "
                    "loss of function."
                ),
            ),
            when_to_seek_care=(
                "Seek medical review for severe, rapidly "
                "worsening, or function-limiting symptoms."
            ),
            questions=(
                (
                    "Are there activity restrictions "
                    "while this injury improves?"
                ),
            ),
        ),
    )

    @classmethod
    def _profile_for(
        cls,
        text: str,
    ) -> GuidanceProfile | None:
        normalized = (
            " ".join(
                text.lower().split()
            )
        )

        for profile in cls.PROFILES:
            if any(
                re.search(
                    pattern,
                    normalized,
                    flags=re.IGNORECASE,
                )
                for pattern
                in profile.patterns
            ):
                return profile

        return None

    @classmethod
    def _build_profile_card(
        cls,
        topic: str,
        status: str | None,
        sources: list[
            SourceEvidence
        ],
        profile: GuidanceProfile,
        category: str,
    ) -> MedicalGuidanceCard:
        fact_value = topic

        if status:
            fact_value = (
                f"{topic} "
                f"(documented status: {status})"
            )

        return MedicalGuidanceCard(
            topic=topic,
            documented_fact=(
                DocumentedMedicalFact(
                    category=category,
                    label="Documented finding",
                    value=fact_value,
                    sources=sources,
                )
            ),
            plain_language_explanation=(
                profile.explanation
            ),
            general_information=list(
                profile.general_information
            ),
            supportive_care=list(
                profile.supportive_care
            ),
            red_flags=list(
                profile.red_flags
            ),
            when_to_seek_care=(
                profile.when_to_seek_care
            ),
            questions_for_clinician=list(
                profile.questions
            ),
            guidance_level=(
                GuidanceLevel.SUPPORTIVE
            ),
            safety_flags=list(
                cls.SAFETY_FLAGS
            ),
            sources=sources,
        )

    @classmethod
    def _generic_diagnosis_card(
        cls,
        name: str,
        status: str,
        sources: list[
            SourceEvidence
        ],
    ) -> MedicalGuidanceCard:
        return MedicalGuidanceCard(
            topic=name,
            documented_fact=(
                DocumentedMedicalFact(
                    category="diagnosis",
                    label=(
                        "Documented diagnosis"
                    ),
                    value=(
                        f"{name} "
                        f"(status: {status})"
                    ),
                    sources=sources,
                )
            ),
            plain_language_explanation=(
                "The uploaded record lists "
                f"“{name}” as a diagnosis. MIRA is "
                "reporting that documented diagnosis "
                "rather than determining a new one "
                "from symptoms."
            ),
            general_information=[
                (
                    "The precise meaning, severity, "
                    "cause, and treatment implications "
                    "depend on the clinical context in "
                    "the record and the treating team."
                ),
            ],
            supportive_care=[],
            red_flags=[],
            when_to_seek_care=None,
            questions_for_clinician=[
                (
                    "What does this documented diagnosis "
                    "mean in the context of this record?"
                ),
                (
                    "Are there follow-up steps already "
                    "recommended for this diagnosis?"
                ),
            ],
            guidance_level=(
                GuidanceLevel.EDUCATION
            ),
            safety_flags=list(
                cls.SAFETY_FLAGS
            ),
            sources=sources,
        )

    @classmethod
    def build_cards(
        cls,
        extraction: (
            MedicalDocumentExtraction
        ),
    ) -> list[MedicalGuidanceCard]:
        cards: list[
            MedicalGuidanceCard
        ] = []

        seen_topics: set[str] = set()

        for diagnosis in (
            extraction.diagnoses
        ):
            key = (
                diagnosis.name
                .strip()
                .casefold()
            )

            if not key or key in seen_topics:
                continue

            profile = cls._profile_for(
                diagnosis.name
            )

            if profile is not None:
                card = (
                    cls._build_profile_card(
                        topic=diagnosis.name,
                        status=(
                            diagnosis.status.value
                        ),
                        sources=(
                            diagnosis.sources
                        ),
                        profile=profile,
                        category="diagnosis",
                    )
                )
            else:
                card = (
                    cls._generic_diagnosis_card(
                        name=diagnosis.name,
                        status=(
                            diagnosis.status.value
                        ),
                        sources=(
                            diagnosis.sources
                        ),
                    )
                )

            cards.append(card)
            seen_topics.add(key)

        for procedure in (
            extraction.procedures
        ):
            profile = cls._profile_for(
                procedure.name
            )

            if profile is None:
                continue

            key = (
                procedure.name
                .strip()
                .casefold()
            )

            if key in seen_topics:
                continue

            cards.append(
                cls._build_profile_card(
                    topic=procedure.name,
                    status=None,
                    sources=(
                        procedure.sources
                    ),
                    profile=profile,
                    category="procedure",
                )
            )

            seen_topics.add(key)

        return cards