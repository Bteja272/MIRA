import time

from app.services.conversation_memory_service import (
    ConversationMemoryService,
)
from app.services.llm_service import (
    LLMService,
)
from app.services.medical_prompt_service import (
    MedicalPromptService,
)


class DirectLLMService:
    @staticmethod
    def query(
        query: str,
        conversation_context: (
            list[dict[str, str]]
            | None
        ) = None,
    ) -> dict:
        started_at = (
            time.perf_counter()
        )

        conversation_query = (
            ConversationMemoryService
            .build_prompt_query(
                query=query,
                context=(
                    conversation_context
                ),
            )
        )

        prompt = f"""
Answer the following medical-information question clearly and
educationally.

Conversation history, when present, is supplied only for continuity
and reference resolution. Do not treat previous assistant messages as
medical evidence or as verified personal medical history.

Do not diagnose the user, prescribe medication, recommend medication
changes, or provide a definite prognosis.

{conversation_query}
""".strip()

        answer = (
            LLMService
            .generate_response(
                prompt=prompt,
                system_prompt=(
                    MedicalPromptService
                    .general_system_prompt()
                ),
            )
        )

        answer = (
            MedicalPromptService
            .ensure_disclaimer(answer)
        )

        return {
            "query": query,
            "answer": answer,
            "sources": [],
            "latency_seconds": round(
                (
                    time.perf_counter()
                    - started_at
                ),
                3,
            ),
        }