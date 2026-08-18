import unittest

from evaluation.safety_metrics import (
    aggregate_routing_cases,
    aggregate_safety_cases,
    normalize_label,
)


class SafetyMetricTests(
    unittest.TestCase
):
    def test_category_aliases_normalize(
        self,
    ) -> None:
        self.assertEqual(
            normalize_label(
                "symptom-diagnosis"
            ),
            "diagnosis",
        )
        self.assertEqual(
            normalize_label(
                "medication-change"
            ),
            "medication_change",
        )
        self.assertEqual(
            normalize_label(
                "self-harm"
            ),
            "self_harm",
        )

    def test_safety_aggregate(
        self,
    ) -> None:
        results = [
            {
                "expected_allowed": False,
                "actual_allowed": False,
                "decision_correct": True,
                "category_correct": True,
                "latency_ms": 1.0,
            },
            {
                "expected_allowed": True,
                "actual_allowed": True,
                "decision_correct": True,
                "category_correct": True,
                "latency_ms": 2.0,
            },
        ]

        summary = aggregate_safety_cases(
            results
        )

        self.assertEqual(
            summary[
                "unsafe_block_recall"
            ],
            1.0,
        )
        self.assertEqual(
            summary[
                "benign_false_positive_rate"
            ],
            0.0,
        )
        self.assertEqual(
            summary[
                "decision_accuracy"
            ],
            1.0,
        )

    def test_route_aggregate(
        self,
    ) -> None:
        summary = (
            aggregate_routing_cases(
                [
                    {
                        "route_correct": True,
                        "latency_ms": 1.0,
                    },
                    {
                        "route_correct": True,
                        "latency_ms": 1.5,
                    },
                ]
            )
        )

        self.assertEqual(
            summary["route_accuracy"],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()