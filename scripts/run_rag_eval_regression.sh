#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

echo "MIRA RAG Evaluation Regression"
echo "=============================="

python -m pytest \
  tests/test_rag_evaluation.py \
  tests/test_live_retrieval_runner.py \
  tests/test_generation_evaluator.py \
  tests/test_generation_evaluator_regressions.py \
  tests/test_generation_abstention_regressions.py \
  tests/test_final_rag_runner.py \
  tests/test_end_to_end_evaluator.py \
  tests/test_rag_evaluation_report.py \
  -v

echo
echo "RAG evaluation regression passed."