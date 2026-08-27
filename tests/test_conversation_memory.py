import unittest
from unittest.mock import patch

from app.services.conversation_memory_service import (
    ConversationMemoryService,
)
from app.services.conversation_service import (
    ConversationService,
)
from app.services.langgraph_agent_service import (
    safety_node,
)
from app.services.medical_prompt_service import (
    MedicalPromptService,
)


class ConversationMemoryTests(
    unittest.TestCase
):
    def test_standalone_query_is_not_rewritten(
        self,
    ):
        query = (
            "What is hypertension?"
        )

        result = (
            ConversationMemoryService
            .build_retrieval_query(
                query=query,
                context=[],
            )
        )

        self.assertEqual(
            result,
            query,
        )

    def test_non_follow_up_is_not_rewritten(
        self,
    ):
        context = [
            {
                "role": "user",
                "content": (
                    "What medications "
                    "are listed?"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Metformin is listed."
                ),
            },
        ]

        query = (
            "Explain systolic blood "
            "pressure."
        )

        result = (
            ConversationMemoryService
            .build_retrieval_query(
                query=query,
                context=context,
            )
        )

        self.assertEqual(
            result,
            query,
        )

    def test_follow_up_uses_previous_user_question(
        self,
    ):
        context = [
            {
                "role": "user",
                "content": (
                    "What medications "
                    "are listed?"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Metformin and "
                    "Lisinopril are listed."
                ),
            },
        ]

        query = (
            "What is the dose of "
            "the first one?"
        )

        result = (
            ConversationMemoryService
            .build_retrieval_query(
                query=query,
                context=context,
            )
        )

        self.assertIn(
            "What medications are listed?",
            result,
        )

        self.assertIn(
            query,
            result,
        )

    def test_retrieval_does_not_use_assistant_answer(
        self,
    ):
        assistant_content = (
            "GENERATED ASSISTANT CONTENT "
            "THAT MUST NOT BECOME "
            "RETRIEVAL EVIDENCE"
        )

        context = [
            {
                "role": "user",
                "content": (
                    "What medications "
                    "are listed?"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    assistant_content
                ),
            },
        ]

        result = (
            ConversationMemoryService
            .build_retrieval_query(
                query=(
                    "What about the "
                    "first one?"
                ),
                context=context,
            )
        )

        self.assertIn(
            "What medications are listed?",
            result,
        )

        self.assertNotIn(
            assistant_content,
            result,
        )

    def test_prompt_context_identifies_history_as_untrusted(
        self,
    ):
        context = [
            {
                "role": "user",
                "content": (
                    "What medications "
                    "are listed?"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Example previous "
                    "response."
                ),
            },
        ]

        result = (
            ConversationMemoryService
            .format_context(
                context
            )
        )

        self.assertIn(
            "CONVERSATION CONTEXT",
            result,
        )

        self.assertIn(
            (
                "Do not treat previous "
                "assistant messages as "
                "medical evidence."
            ),
            result,
        )

        self.assertIn(
            (
                "User: What medications "
                "are listed?"
            ),
            result,
        )

        self.assertIn(
            (
                "MIRA: Example previous "
                "response."
            ),
            result,
        )

    def test_assistant_disclaimer_is_removed_from_context(
        self,
    ):
        answer = (
            "The document lists "
            "the requested information."
            "\n\n"
            + MedicalPromptService
            .DISCLAIMER
        )

        cleaned = (
            ConversationService
            ._context_content(
                answer,
                "assistant",
            )
        )

        self.assertEqual(
            cleaned,
            (
                "The document lists "
                "the requested information."
            ),
        )

        self.assertNotIn(
            MedicalPromptService
            .DISCLAIMER,
            cleaned,
        )

    def test_context_message_is_bounded(
        self,
    ):
        with patch.object(
            ConversationService,
            (
                "MAX_CONTEXT_"
                "MESSAGE_CHARACTERS"
            ),
            20,
        ):
            cleaned = (
                ConversationService
                ._context_content(
                    "x" * 100,
                    "user",
                )
            )

        self.assertLessEqual(
            len(cleaned),
            23,
        )

        self.assertTrue(
            cleaned.endswith(
                "..."
            )
        )

    def test_conversation_title_is_bounded(
        self,
    ):
        title = (
            ConversationService
            ._clean_title(
                "x" * 500
            )
        )

        self.assertLessEqual(
            len(title),
            100,
        )

        self.assertTrue(
            title.endswith(
                "..."
            )
        )

    @patch(
        "app.services."
        "langgraph_agent_service."
        "_run_safety_guard"
    )
    def test_safety_guard_receives_only_current_query(
        self,
        mock_safety_guard,
    ):
        mock_safety_guard.return_value = {
            "allowed": True,
            "category": "allowed",
            "response": "",
        }

        state = {
            "query": (
                "Explain this result."
            ),
            "conversation_context": [
                {
                    "role": "user",
                    "content": (
                        "Previous medical "
                        "conversation content"
                    ),
                }
            ],
        }

        result = safety_node(
            state
        )

        mock_safety_guard.assert_called_once_with(
            "Explain this result."
        )

        self.assertEqual(
            result[
                "safety_status"
            ],
            "allowed",
        )


if __name__ == "__main__":
    unittest.main()