import unittest
from unittest.mock import patch

from app.services.llm_providers.base import (
    LLMProviderError,
)
from app.services.llm_providers.retry_policy import (
    LLMRetryPolicy,
)


class LLMRetryPolicyTests(
    unittest.TestCase
):
    def test_exponential_delay_is_capped(
        self,
    ) -> None:
        policy = LLMRetryPolicy(
            max_retries=4,
            base_delay_seconds=0.5,
            max_delay_seconds=1.0,
            retry_after_cap_seconds=5.0,
        )
        error = LLMProviderError(
            "groq",
            "temporary",
            retryable=True,
        )

        self.assertEqual(
            policy.delay_seconds(
                retry_number=1,
                error=error,
            ),
            0.5,
        )
        self.assertEqual(
            policy.delay_seconds(
                retry_number=2,
                error=error,
            ),
            1.0,
        )
        self.assertEqual(
            policy.delay_seconds(
                retry_number=4,
                error=error,
            ),
            1.0,
        )

    def test_retry_after_is_capped(
        self,
    ) -> None:
        policy = LLMRetryPolicy(
            max_retries=1,
            base_delay_seconds=0.25,
            max_delay_seconds=2.0,
            retry_after_cap_seconds=3.0,
        )
        error = LLMProviderError(
            "groq",
            "rate limited",
            retryable=True,
            retry_after_seconds=10.0,
        )

        self.assertEqual(
            policy.delay_seconds(
                retry_number=1,
                error=error,
            ),
            3.0,
        )

    @patch.dict(
        "os.environ",
        {
            "LLM_PROVIDER_MAX_RETRIES": "2",
            "LLM_PROVIDER_RETRY_BASE_DELAY_SECONDS": "0.1",
            "LLM_PROVIDER_RETRY_MAX_DELAY_SECONDS": "1.5",
            "LLM_PROVIDER_RETRY_AFTER_CAP_SECONDS": "4",
        },
        clear=False,
    )
    def test_policy_loads_from_environment(
        self,
    ) -> None:
        policy = (
            LLMRetryPolicy
            .from_environment()
        )

        self.assertEqual(
            policy.max_retries,
            2,
        )
        self.assertEqual(
            policy.base_delay_seconds,
            0.1,
        )
        self.assertEqual(
            policy.max_delay_seconds,
            1.5,
        )
        self.assertEqual(
            policy.retry_after_cap_seconds,
            4.0,
        )


if __name__ == "__main__":
    unittest.main()