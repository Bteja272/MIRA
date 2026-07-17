from typing import Any


class PromptService:
    @staticmethod
    def _build_source_block(
        document: Any,
        source_number: int,
    ) -> str:
        metadata = getattr(
            document,
            "metadata",
            {},
        ) or {}

        source = metadata.get(
            "source",
            "Unknown source",
        )
        page_number = metadata.get("page_number")
        chunk_index = metadata.get("chunk_index")
        similarity_score = metadata.get(
            "similarity_score"
        )

        details = [
            f"Source: {source}",
        ]

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

        metadata_text = " | ".join(details)

        return (
            f"[Source {source_number}]\n"
            f"{metadata_text}\n"
            f"{document.page_content.strip()}"
        )

    @classmethod
    def build_prompt(
        cls,
        query: str,
        documents: list[Any],
        task: str = "qa",
    ) -> str:
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

        context = "\n\n".join(source_blocks)

        if task == "summarization":
            task_instruction = """
The supplied chunks represent the complete indexed document.

Produce a clear summary of the document.

General instructions:

- Combine information across all chunks.
- Remove duplication caused by overlapping chunks.
- Preserve dates, names, diagnoses, medication names, dosages,
  instructions, and numerical values exactly as documented.
- Do not state that the context is incomplete merely because the
  document is divided into multiple chunks.
- Place source citations directly after the facts they support.
- Do not place empty source markers at the end.

For laboratory reports:

- Use one bullet for each laboratory test.
- Copy the test name exactly.
- Copy the result and unit exactly.
- Copy the reference range exactly.
- Copy the documented flag exactly.
- Do not calculate whether a result is above, below, or within range.
- Do not reinterpret High, Low, or Normal flags.
- Do not merge neighboring laboratory tests.

Preferred laboratory format:

- <Test name>
  Result: <documented result and unit>
  Reference range: <documented range>
  Documented flag: <documented flag>
""".strip()
        else:
            task_instruction = """
Answer the user's question using only the supplied document context.

Instructions:

- Cite the source immediately after the supported statement.
- Preserve numerical values, units, dates, medication names, dosages,
  reference ranges, and documented flags exactly.
- Do not invent missing information.
- For laboratory information, do not independently classify values as
  high, low, normal, above, below, or within range.
- When the requested information is not documented, state that it is
  not documented in the supplied context.
""".strip()

        return f"""
TASK
{task_instruction}

DOCUMENT CONTEXT
{context}

USER QUESTION
{query}

ANSWER
""".strip()