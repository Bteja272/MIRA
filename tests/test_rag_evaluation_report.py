from evaluation.rag_evaluation_report import (
    build_markdown_report,
)


def _retrieval_report():
    return {
        "dataset_name": (
            "mira_rag_eval_v1"
        ),
        "dataset_version": (
            "1.0.0"
        ),
        "context_token_budget": 12000,
        "retrieval": {
            "case_count": 9,
            "hit_rate_at_k": 1.0,
            "recall_at_k": 1.0,
            "mrr": 0.944,
            "wrong_document_rate": (
                0.037
            ),
            "by_task": {
                "qa": {
                    "case_count": 9,
                    "hit_rate_at_k": 1.0,
                    "recall_at_k": 1.0,
                    "mrr": 0.944,
                    "wrong_document_rate": (
                        0.037
                    ),
                }
            },
        },
        "context": {
            "case_count": 12,
            "document_recall": 1.0,
            "required_fact_survival_rate": (
                1.0
            ),
            "evidence_retention_rate": (
                1.0
            ),
        },
        "context_cases": [
            {
                "case_id": (
                    "qa_medication_lisinopril"
                ),
                "expected_sources": [
                    "medication_list_01.txt"
                ],
            },
            {
                "case_id": (
                    "distractor_glucose"
                ),
                "expected_sources": [
                    "lab_report_01.txt"
                ],
            },
            {
                "case_id": (
                    "comparison_glucose"
                ),
                "expected_sources": [
                    "lab_report_01.txt",
                    "followup_lab_01.txt",
                ],
            },
            {
                "case_id": (
                    "summary_discharge"
                ),
                "expected_sources": [
                    "discharge_summary_01.txt"
                ],
            },
        ],
    }


def _final_report():
    return {
        "dataset_name": (
            "mira_rag_eval_v1"
        ),
        "dataset_version": (
            "1.0.0"
        ),
        "generation_summary": {
            "case_count": 12,
            "required_fact_recall": (
                0.958
            ),
            "forbidden_fact_violation_rate": (
                0.083
            ),
            "abstention_accuracy": 1.0,
            "grounded_answer_pass_rate": (
                1.0
            ),
            "missing_source_citation_rate": (
                0.0
            ),
            "unsupported_medical_value_rate": (
                0.0
            ),
            "invalid_citation_rate": (
                0.0
            ),
            "uncited_medical_value_rate": (
                0.0
            ),
            "misattributed_medical_value_rate": (
                0.0
            ),
            "case_pass_rate": (
                0.833
            ),
        },
        "cases": [
            {
                "case_id": (
                    "qa_medication_lisinopril"
                ),
                "evaluation": {
                    "missing_required_facts": [
                        "once daily"
                    ],
                    "forbidden_facts_found": [],
                },
            },
            {
                "case_id": (
                    "distractor_glucose"
                ),
                "evaluation": {
                    "missing_required_facts": [],
                    "forbidden_facts_found": [
                        "96 mg/dL"
                    ],
                },
            },
        ],
    }


def _end_to_end_report():
    return {
        "dataset_name": (
            "mira_rag_eval_v1"
        ),
        "dataset_version": (
            "1.0.0"
        ),
        "summary": {
            "case_count": 12,
            "success_count": 10,
            "success_rate": (
                0.833
            ),
            "failure_counts": {
                "forbidden_fact": 1,
                "generation_incomplete": 1,
            },
            "by_task": {
                "comparison": {
                    "case_count": 2,
                    "success_count": 2,
                    "success_rate": 1.0,
                },
                "qa": {
                    "case_count": 9,
                    "success_count": 7,
                    "success_rate": (
                        0.778
                    ),
                },
                "summarization": {
                    "case_count": 1,
                    "success_count": 1,
                    "success_rate": 1.0,
                },
            },
        },
        "cases": [
            {
                "case_id": (
                    "qa_medication_lisinopril"
                ),
                "task": "qa",
                "outcome": (
                    "generation_incomplete"
                ),
                "success": False,
            },
            {
                "case_id": (
                    "distractor_glucose"
                ),
                "task": "qa",
                "outcome": (
                    "forbidden_fact"
                ),
                "success": False,
            },
        ],
    }


def test_report_contains_core_metrics():
    report = build_markdown_report(
        retrieval_report=(
            _retrieval_report()
        ),
        final_report=(
            _final_report()
        ),
        end_to_end_report=(
            _end_to_end_report()
        ),
        retrieval_report_path=(
            "rag_retrieval.json"
        ),
        final_report_path=(
            "rag_final.json"
        ),
        end_to_end_report_path=(
            "rag_end_to_end.json"
        ),
    )

    assert (
        "# MIRA RAG Evaluation Report"
        in report
    )

    assert (
        "| Hit@3 | 1.000 |"
        in report
    )

    assert (
        "| MRR | 0.944 |"
        in report
    )

    assert (
        "| Required Fact Recall | "
        "0.958 |"
        in report
    )

    assert (
        "| End-to-end success rate | "
        "0.833 |"
        in report
    )


def test_report_contains_failure_analysis():
    report = build_markdown_report(
        retrieval_report=(
            _retrieval_report()
        ),
        final_report=(
            _final_report()
        ),
        end_to_end_report=(
            _end_to_end_report()
        ),
        retrieval_report_path=(
            "rag_retrieval.json"
        ),
        final_report_path=(
            "rag_final.json"
        ),
        end_to_end_report_path=(
            "rag_end_to_end.json"
        ),
    )

    assert (
        "`qa_medication_lisinopril`"
        in report
    )

    assert (
        "`generation_incomplete`"
        in report
    )

    assert (
        "`once daily`"
        in report
    )

    assert (
        "`distractor_glucose`"
        in report
    )

    assert (
        "`forbidden_fact`"
        in report
    )

    assert (
        "`96 mg/dL`"
        in report
    )


def test_report_contains_limitations():
    report = build_markdown_report(
        retrieval_report=(
            _retrieval_report()
        ),
        final_report=(
            _final_report()
        ),
        end_to_end_report=(
            _end_to_end_report()
        ),
        retrieval_report_path=(
            "rag_retrieval.json"
        ),
        final_report_path=(
            "rag_final.json"
        ),
        end_to_end_report_path=(
            "rag_end_to_end.json"
        ),
    )

    assert (
        "small and synthetic"
        in report
    )

    assert (
        "selected-document RAG"
        in report
    )

    assert (
        "HIPAA compliance"
        in report
    )


def test_report_contains_source_artifacts():
    report = build_markdown_report(
        retrieval_report=(
            _retrieval_report()
        ),
        final_report=(
            _final_report()
        ),
        end_to_end_report=(
            _end_to_end_report()
        ),
        retrieval_report_path=(
            "/tmp/rag_retrieval.json"
        ),
        final_report_path=(
            "/tmp/rag_final.json"
        ),
        end_to_end_report_path=(
            "/tmp/rag_end_to_end.json"
        ),
    )

    assert (
        "`rag_retrieval.json`"
        in report
    )

    assert (
        "`rag_final.json`"
        in report
    )

    assert (
        "`rag_end_to_end.json`"
        in report
    )