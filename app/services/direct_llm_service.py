import time

from app.services.llm_service import LLMService
from app.services.medical_prompt_service import (
    MedicalPromptService,
)


class DirectLLMService:
    @staticmethod
    def query(
        query: str,
    ) -> dict:
        started_at = time.perf_counter()

        prompt = f"""
Answer the following medical-information question clearly and
educationally.

Do not diagnose the user, prescribe medication, recommend medication
changes, or provide a definite prognosis.

Question:
{query}
""".strip()

        answer = LLMService.generate_response(
            prompt=prompt,
            system_prompt=(
                MedicalPromptService
                .general_system_prompt()
            ),
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
                time.perf_counter() - started_at,
                3,
            ),
        }