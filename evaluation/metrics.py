from __future__ import annotations

from collections import defaultdict
from statistics import mean

from evaluation.models import RetrievalCaseResult


def aggregate_retrieval_results(
    results: list[RetrievalCaseResult],
) -> dict:
    if not results:
        return {
            "case_count": 0,
            "hit_rate_at_k": 0.0,
            "recall_at_k": 0.0,
            "mrr": 0.0,
            "wrong_document_rate": 0.0,
            "by_task": {},
        }

    by_task: dict[str, list[RetrievalCaseResult]] = defaultdict(list)
    for result in results:
        by_task[result.task].append(result)

    def summarize(task_results: list[RetrievalCaseResult]) -> dict:
        return {
            "case_count": len(task_results),
            "hit_rate_at_k": mean(
                1.0 if result.hit_at_k else 0.0
                for result in task_results
            ),
            "recall_at_k": mean(
                result.recall_at_k
                for result in task_results
            ),
            "mrr": mean(
                result.reciprocal_rank
                for result in task_results
            ),
            "wrong_document_rate": mean(
                result.wrong_document_rate
                for result in task_results
            ),
        }

    return {
        **summarize(results),
        "by_task": {
            task: summarize(task_results)
            for task, task_results in sorted(by_task.items())
        },
    }
