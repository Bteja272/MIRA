from typing import Any


class PromptService:
    @staticmethod
    def _build_source_block(
        document: Any,
        source_number: int,
    ) -> str:
        """
        Convert one retrieved LangChain document into a clearly
        identified source block for the LLM.

        For multi-document queries, document_position preserves the
        order in which the user selected the documents.
        """
        metadata = getattr(
            document,
            "metadata",
            {},
        ) or {}

        source = metadata.get(
            "source",
            "Unknown source",
        )

        document_id = metadata.get(
            "document_id",
            "Unknown document",
        )

        document_type = metadata.get(
            "document_type",
            "unknown",
        )

        document_position = metadata.get(
            "document_position"
        )

        page_number = metadata.get(
            "page_number"
        )

        chunk_index = metadata.get(
            "chunk_index"
        )

        similarity_score = metadata.get(
            "similarity_score"
        )

        details = [
            f"Document: {source}",
            f"Document ID: {document_id}",
            f"Document type: {document_type}",
        ]

        if document_position is not None:
            details.append(
                f"Selected document: {document_position}"
            )

        if page_number is not None:
            details.append(
                f"Page: {page_number}"
            )

        if chunk_index is not None:
            details.append(
                f"Chunk: {chunk_index}"
            )

        if similarity_score is not None:
            details.append(
                f"Similarity: {similarity_score}"
            )

        metadata_text = " | ".join(
            details
        )

        return (
            f"[Source {source_number}]\n"
            f"{metadata_text}\n"
            f"{document.page_content.strip()}"
        )

    @staticmethod
    def _task_instruction(
        task: str,
    ) -> str:
        """
        Return instructions for the requested RAG task.
        """
        if task == "comparison":
            return """
Compare the selected medical documents using only the supplied context.

Required structure:

1. Give each document its own heading using its filename.
2. Summarize the documented diagnoses, results, medications,
   instructions, procedures, and dates for that document.
3. Add a final section named "Cross-document comparison."
4. Identify documented similarities and differences.
5. Describe changes over time only when the documents contain dates
   and directly comparable values.
6. Never infer improvement, deterioration, causation, a new diagnosis,
   or a treatment recommendation.
7. When information is absent from one document, say "not documented"
   rather than guessing.
8. Cite each fact immediately using the source label that supports it.
9. Preserve every number, unit, reference range, medication, dosage,
   documented flag, and date exactly.
10. Do not combine facts from different patients or documents.
""".strip()

        if task == "multi_document_overview":
            return """
Create a combined overview of all selected medical documents.

Required structure:

1. Give each document its own heading using its filename.
2. Summarize the major documented information in each document.
3. Add a final section named "Combined overview."
4. Organize the combined overview under useful headings such as:
   diagnoses, laboratory results, medications, procedures, and
   follow-up instructions.
5. Do not merge facts from different documents without identifying
   which document supports each fact.
6. Do not infer a diagnosis, prognosis, treatment recommendation, or
   causal relationship.
7. When information is absent, say "not documented."
8. Cite each fact immediately using the source label that supports it.
9. Preserve every number, unit, reference range, medication, dosage,
   documented flag, and date exactly.
""".strip()

        if task == "summarization":
            return """
The supplied chunks represent one complete indexed document.

Produce a clear summary of the document.

General instructions:

- Combine information across all chunks.
- Remove duplication caused by overlapping chunks.
- Preserve dates, names, diagnoses, medication names, dosages,
  instructions, and numerical values exactly as documented.
- Do not state that the context is incomplete merely because the
  document is divided into multiple chunks.
- Cite facts immediately using the supporting source label.
- Do not place empty source markers at the end.

For laboratory reports:

- Use one bullet for each laboratory test.
- Copy the test name exactly.
- Copy the result and unit exactly.
- Copy the reference range exactly.
- Copy the documented flag exactly.
- Do not independently calculate whether a result is above, below,
  normal, abnormal, or within range.
- Do not reinterpret High, Low, or Normal flags.
- Do not merge neighboring laboratory tests.
""".strip()

        return """
Answer the user's question using only the supplied document context.

Instructions:

- Cite each fact immediately using the source label that supports it.
- Preserve numerical values, units, dates, medication names, dosages,
  reference ranges, and documented flags exactly.
- Do not invent missing information.
- Do not independently classify laboratory values as high, low,
  normal, above, below, or within range.
- When the requested information is absent, state that it is not
  documented in the supplied context.
""".strip()

    @classmethod
    def build_prompt(
        cls,
        query: str,
        documents: list[Any],
        task: str = "qa",
    ) -> str:
        """
        Build the final grounded prompt for single- or multi-document
        retrieval.
        """
        source_blocks = [
            cls._build_source_block(
                document=document,
                source_number=index,
            )
            for index, document in enumerate(
                documents,
                start=1,
            )
        ]

        context = "\n\n".join(
            source_blocks
        )

        task_instruction = (
            cls._task_instruction(
                task
            )
        )

        return f"""
TASK
{task_instruction}

DOCUMENT CONTEXT
{context}

USER QUESTION
{query}

ANSWER
""".strip()