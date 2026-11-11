# MIRA RAG Evaluation

MIRA includes a separate evaluation harness for measuring retrieval quality, context preservation, grounded generation, citation behavior, abstention behavior, and end-to-end RAG performance.

The evaluation corpus contains synthetic medical records only. It is not a clinical benchmark and must not be interpreted as evidence of clinical efficacy, diagnostic accuracy, HIPAA compliance, or suitability for autonomous medical decision-making.

## Dataset

Current dataset:

```text
mira_rag_eval_v1 1.0.0
```

Synthetic documents:

```text
evaluation/datasets/synthetic_medical_docs/
├── discharge_summary_01.txt
├── followup_lab_01.txt
├── lab_report_01.txt
└── medication_list_01.txt
```

Evaluation cases are defined in:

```text
evaluation/datasets/rag_eval_cases.json
```

The current dataset contains 12 cases covering:

- document question answering
- cross-document comparison
- summarization
- missing-information abstention
- distractor-document resistance

## Evaluation Layers

The evaluation is intentionally separated into multiple layers.

### Retrieval

`evaluation/live_retrieval_runner.py`

Measures:

- Hit@K
- Recall@K
- Mean Reciprocal Rank
- wrong-document rate
- context document recall
- required-fact survival
- expected-evidence retention

Current baseline:

```text
QA cases:                  9
Hit@3:                     1.000
Recall@3:                  1.000
MRR:                       0.944
Wrong-document rate:       0.037

Context document recall:   1.000
Required-fact survival:    1.000
Evidence retention:        1.000
```

Baseline report:

```text
evaluation/reports/rag_retrieval_eval_20260907T184318Z.json
```

### Final Production RAG

`evaluation/final_rag_runner.py`

This runner calls the normal production `RAGService` and evaluates the final response after the application's validation, repair, fallback, and disclaimer behavior.

Current baseline:

```text
Required Fact Recall:              0.958
Forbidden Fact Violation Rate:     0.083
Abstention Accuracy:               1.000
Grounded Answer Pass Rate:         1.000
Missing Source Citation Rate:      0.000
Unsupported Medical Value Rate:    0.000
Invalid Citation Rate:             0.000
Uncited Medical Value Rate:        0.000
Misattributed Medical Value Rate:  0.000
Case Pass Rate:                    0.833
```

Baseline report:

```text
evaluation/reports/rag_final_eval_20261111T000459Z.json
```

### End-to-End Evaluation

`evaluation/end_to_end_runner.py`

The end-to-end evaluator combines retrieval/context and final-generation reports without rerunning the LLM.

Failure classifications are ordered by pipeline stage:

```text
execution_failure
retrieval_failure
context_loss
grounding_failure
abstention_failure
forbidden_fact
generation_incomplete
success
```

Current baseline:

```text
Cases:          12
Successful:     10
Success Rate:   0.833

comparison:     2/2
qa:             7/9
summarization:  1/1
```

Known failures:

```text
qa_medication_lisinopril
→ generation_incomplete
→ answer included 10 mg but omitted "once daily"

distractor_glucose
→ forbidden_fact
→ fallback included distractor value 96 mg/dL
```

Baseline report:

```text
evaluation/reports/rag_end_to_end_eval_20261111T002654Z.json
```

## Consolidated Report

Generate the human-readable report with:

```bash
python -m evaluation.rag_evaluation_report \
  --retrieval-report evaluation/reports/rag_retrieval_eval_20260907T184318Z.json \
  --final-report evaluation/reports/rag_final_eval_20261111T000459Z.json \
  --end-to-end-report evaluation/reports/rag_end_to_end_eval_20261111T002654Z.json
```

Output:

```text
evaluation/reports/RAG_EVALUATION_REPORT.md
```

## Regression Suite

Routine regression testing should not require an LLM provider or a new live benchmark run.

Run:

```bash
./scripts/run_rag_eval_regression.sh
```

The regression suite validates:

- dataset/evaluation contracts
- retrieval metrics
- generation metrics
- citation validation
- abstention phrase handling
- negated forbidden-fact handling
- final-RAG runner behavior
- end-to-end failure classification
- consolidated report generation

## Running a New Live Retrieval Benchmark

A live retrieval run requires the synthetic documents to already be ingested for the evaluation user.

Example:

```bash
python -m evaluation.live_retrieval_runner \
  --user-id "<EVALUATION_USER_ID>" \
  --top-k 3 \
  --context-token-budget 12000
```

## Running a New Final Production-RAG Benchmark

A final production-RAG run invokes the configured LLM provider and can therefore be affected by provider availability, rate limits, latency, and model nondeterminism.

```bash
python -m evaluation.final_rag_runner \
  --user-id "<EVALUATION_USER_ID>"
```

Do not expect generation metrics to be identical across independent runs.

Preserve completed JSON reports so results remain inspectable without rerunning the LLM.

## Benchmark Scope

The current benchmark is intentionally limited.

Most cases evaluate explicitly selected documents, matching MIRA's primary document-Q&A workflow. It should not be described as a large-scale corpus-wide retrieval benchmark.

The synthetic corpus currently contains four documents, so distractor diversity is limited.

The benchmark is useful for engineering regression detection and for measuring MIRA's current RAG pipeline, but it is not a substitute for clinical validation.