class PromptService:
    @staticmethod
    def build_prompt(
        query: str,
        context_chunks: list[dict],
        task: str = "question_answering",
    ) -> str:
        formatted_sources = []

        for index, chunk in enumerate(
            context_chunks,
            start=1,
        ):
            page_number = chunk.get("page_number")
            page_display = (
                str(page_number)
                if page_number is not None
                else "N/A"
            )

            formatted_sources.append(
                f"""
[Source {index}]
Filename: {chunk.get("source", "Unknown")}
Document ID: {chunk.get("document_id", "Unknown")}
Page: {page_display}
Chunk index: {chunk.get("chunk_index", "Unknown")}
Content:
{chunk["text"]}
""".strip()
            )

        context_text = "\n\n".join(formatted_sources)

        if task == "summarization":
            task_instruction = """
Produce a clear summary of the complete provided document context.
Combine information across all chunks and avoid repeating overlapping text.
Organize the summary by the document's major topics.
"""
        else:
            task_instruction = """
Answer the user's question using the relevant provided excerpts.
"""

        prompt = f"""
You are an AI assistant that answers questions using uploaded documents.

Instructions:
- Use only information contained in the provided context.
- {task_instruction.strip()}
- Cite supporting information using labels such as [Source 1].
- Do not claim that no document was uploaded when context is provided.
- If the context is incomplete, say that the provided excerpts are
  insufficient to answer fully.
- Do not invent facts that are absent from the context.

Context:
{context_text}

User question:
{query}

Answer:
"""

        return prompt.strip()