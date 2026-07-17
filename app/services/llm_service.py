import requests

from app.core.config import settings


class LLMService:
    DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."

    @staticmethod
    def generate_response(
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        if settings.llm_provider.lower() != "ollama":
            raise ValueError(
                f"Unsupported LLM provider: {settings.llm_provider}"
            )

        url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

        payload = {
            "model": settings.llm_model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        system_prompt
                        or LLMService.DEFAULT_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "stream": False,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=120,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Unable to connect to Ollama at {url}: {exc}"
            ) from exc

        if not response.ok:
            raise RuntimeError(
                f"Ollama request failed with HTTP "
                f"{response.status_code}: {response.text}"
            )

        try:
            data = response.json()
            answer = data["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise RuntimeError(
                f"Unexpected Ollama response: {response.text}"
            ) from exc

        return answer.strip()