import unittest
from unittest.mock import (
    Mock,
    patch,
)

from app.schemas.medical_extraction_strict_schema import (
    MEDICAL_EXTRACTION_CANDIDATE_STRICT_SCHEMA,
)
from app.services.llm_providers.base import (
    LLMRequest,
)
from app.services.llm_providers.groq_provider import (
    GroqProvider,
)


class MedicalExtractionStrictSchemaTests(
    unittest.TestCase
):
    def _assert_strict_schema(
        self,
        schema,
    ) -> None:
        if isinstance(schema, dict):
            if schema.get("type") == "object":
                properties = schema.get(
                    "properties",
                    {},
                )

                self.assertEqual(
                    schema.get(
                        "additionalProperties"
                    ),
                    False,
                )

                self.assertEqual(
                    set(schema.get("required", [])),
                    set(properties.keys()),
                )

            for value in schema.values():
                self._assert_strict_schema(
                    value
                )

        elif isinstance(schema, list):
            for item in schema:
                self._assert_strict_schema(
                    item
                )

    def test_schema_closes_every_object_and_requires_every_field(
        self,
    ) -> None:
        self._assert_strict_schema(
            MEDICAL_EXTRACTION_CANDIDATE_STRICT_SCHEMA
        )

    def test_nullable_fields_use_explicit_null_union(
        self,
    ) -> None:
        patient = (
            MEDICAL_EXTRACTION_CANDIDATE_STRICT_SCHEMA
            ["properties"]["patient"]
        )

        name_schema = (
            patient["properties"]["name"]
        )

        types = {
            item["type"]
            for item in name_schema["anyOf"]
        }

        self.assertEqual(
            types,
            {"string", "null"},
        )


class GroqStrictStructuredOutputTests(
    unittest.TestCase
):
    @patch(
        "app.services.llm_providers."
        "groq_provider.settings"
    )
    @patch(
        "app.services.llm_providers."
        "groq_provider.requests.post"
    )
    def test_groq_sends_strict_json_schema(
        self,
        mock_post,
        mock_settings,
    ) -> None:
        mock_secret = Mock()
        mock_secret.get_secret_value.return_value = (
            "test-groq-key"
        )

        mock_settings.groq_api_key = mock_secret
        mock_settings.groq_base_url = (
            "https://api.groq.com/openai/v1"
        )
        mock_settings.groq_model_name = (
            "openai/gpt-oss-20b"
        )

        response = Mock()
        response.ok = True
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"patient":{},'
                            '"document_date":null}'
                        )
                    }
                }
            ]
        }
        mock_post.return_value = response

        provider = GroqProvider()

        provider.generate(
            LLMRequest(
                prompt="Extract synthetic facts.",
                system_prompt=(
                    "Return structured data."
                ),
                timeout_seconds=30,
                json_mode=True,
                temperature=0.0,
                max_output_tokens=512,
                json_schema=(
                    MEDICAL_EXTRACTION_CANDIDATE_STRICT_SCHEMA
                ),
            )
        )

        _, kwargs = mock_post.call_args
        response_format = (
            kwargs["json"]["response_format"]
        )

        self.assertEqual(
            response_format["type"],
            "json_schema",
        )
        self.assertTrue(
            response_format["json_schema"][
                "strict"
            ]
        )
        self.assertEqual(
            response_format["json_schema"][
                "schema"
            ],
            MEDICAL_EXTRACTION_CANDIDATE_STRICT_SCHEMA,
        )


if __name__ == "__main__":
    unittest.main()