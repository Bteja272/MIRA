MIRA RAG Evaluation

Deterministic evaluation assets for MIRA's RAG pipeline.

All evaluation documents are synthetic. Do not place real patient data,
PHI, production uploads, or conversation content in this directory.

Current metrics

Ranked retrieval

Hit Rate@K

Recall@K

Mean Reciprocal Rank (MRR)

Wrong-document retrieval rate

Context retention

Expected-document recall

Required-fact survival rate

Expected-evidence retained

Generation/grounding evaluation is added in the next 11B stage and will
reuse MIRA's existing ResponseValidationService.

Run:

python -m pytest tests/test_rag_evaluation.py -v