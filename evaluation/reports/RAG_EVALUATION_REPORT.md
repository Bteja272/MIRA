# MIRA RAG Evaluation Report

## Overview

This report summarizes the RAG evaluation results for `mira_rag_eval_v1` version `1.0.0`.

The evaluation uses synthetic medical records only. It measures retrieval quality, context preservation, final production-RAG answer quality, grounding, citation behavior, abstention behavior, and end-to-end case success.

The evaluation harness is separate from the production request path. The final-generation benchmark calls the production RAG service and scores the final answer after the normal validation, repair, and fallback pipeline.

## Dataset

- Dataset: `mira_rag_eval_v1` `1.0.0`
- Evaluation cases: 12
- Synthetic source documents: 4
  - `discharge_summary_01.txt`
  - `followup_lab_01.txt`
  - `lab_report_01.txt`
  - `medication_list_01.txt`

The case set covers:

- document question answering
- cross-document comparison
- document summarization
- missing-information abstention
- distractor-document resistance

## Retrieval Evaluation

| Metric | Result |
| --- | ---: |
| QA retrieval cases | 9 |
| Hit@3 | 1.000 |
| Recall@3 | 1.000 |
| MRR | 0.944 |
| Wrong-document rate | 0.037 |

All evaluated QA retrieval cases contained the expected document within the top-3 results. The non-perfect MRR and wrong-document rate came from the distractor glucose case, where the follow-up laboratory report ranked ahead of the expected laboratory report.

## Context Preservation

| Metric | Result |
| --- | ---: |
| Context cases | 12 |
| Document recall | 1.000 |
| Required-fact survival | 1.000 |
| Expected-evidence retention | 1.000 |

The configured context budget was 12000 estimated tokens. No required evaluation evidence was lost during context construction in this run.

## Final Production-RAG Evaluation

| Metric | Result |
| --- | ---: |
| Required Fact Recall | 0.958 |
| Forbidden Fact Violation Rate | 0.083 |
| Abstention Accuracy | 1.000 |
| Grounded Answer Pass Rate | 1.000 |
| Missing Source Citation Rate | 0.000 |
| Unsupported Medical Value Rate | 0.000 |
| Invalid Citation Rate | 0.000 |
| Uncited Medical Value Rate | 0.000 |
| Misattributed Medical Value Rate | 0.000 |
| Case Pass Rate | 0.833 |

The final production-RAG outputs were fully clean on grounding and citation validation in this run. The remaining failures were content quality failures rather than unsupported or uncited medical-value failures.

## End-to-End Evaluation

| Metric | Result |
| --- | ---: |
| Cases | 12 |
| Successful cases | 10 |
| End-to-end success rate | 0.833 |

### Success by Task

| Task | Passed | Total | Rate |
| --- | ---: | ---: | ---: |
| comparison | 2 | 2 | 1.000 |
| qa | 7 | 9 | 0.778 |
| summarization | 1 | 1 | 1.000 |

## Failure Analysis

### `qa_medication_lisinopril`

- Task: `qa`
- Classification: `generation_incomplete`
- Missing required facts: `once daily`
- Interpretation: retrieval and context preserved the required evidence, but the final answer omitted part of the expected information.

### `distractor_glucose`

- Task: `qa`
- Classification: `forbidden_fact`
- Forbidden facts found: `96 mg/dL`
- Interpretation: the final response included information that the case explicitly marked as distractor content.

## Key Findings

1. Retrieval successfully surfaced the expected source within the configured top-3 window for every evaluated QA retrieval case.
2. Context construction preserved all required evaluation facts and expected evidence in this run.
3. Final answers achieved a grounded answer pass rate of 1.000 with zero unsupported, uncited, invalidly cited, or misattributed medical values according to the deterministic evaluator.
4. End-to-end success was 0.833, with the remaining failures attributed to answer completeness and distractor/fallback behavior.

## Known Limitations

- The benchmark is intentionally small and synthetic. Results should not be interpreted as clinical validation or evidence of safety across real-world medical records.
- Retrieval metrics currently cover the nine QA retrieval cases. Comparison and summarization cases are evaluated through context and final end-to-end behavior rather than the same retrieval metric set.
- Many cases operate over explicitly selected documents. This benchmark therefore evaluates MIRA's selected-document RAG behavior and should not be presented as a broad corpus-wide retrieval benchmark.
- The synthetic corpus contains only 4 documents, so distractor diversity is limited.
- LLM generation is nondeterministic. Provider availability and model variation can change final-answer metrics across runs even when the retrieval inputs are unchanged.
- The distractor glucose failure shows that the deterministic source-grounded fallback can preserve grounding while still returning irrelevant selected-document content.
- These results do not establish HIPAA compliance, clinical efficacy, diagnostic accuracy, or suitability for autonomous medical decision-making.

## Reproducibility

This report was generated from:

- Retrieval report: `rag_retrieval_eval_20260907T184318Z.json`
- Final production-RAG report: `rag_final_eval_20261111T000459Z.json`
- End-to-end report: `rag_end_to_end_eval_20261111T002654Z.json`

Preserving these JSON artifacts makes the reported metrics and failure classifications independently inspectable without rerunning the LLM.
