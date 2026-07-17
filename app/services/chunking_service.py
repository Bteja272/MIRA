from typing import Any

from app.core.config import settings


class TextChunkingService:
    @staticmethod
    def _get_value(document: Any, field_name: str):
        """
        Read a field from either an object or a dictionary.
        """
        if isinstance(document, dict):
            return document.get(field_name)

        return getattr(document, field_name, None)

    @staticmethod
    def _split_long_line(
        line: str,
        chunk_size: int,
    ) -> list[str]:
        """
        Split an unusually long line at word boundaries.
        """
        if len(line) <= chunk_size:
            return [line]

        parts: list[str] = []
        words = line.split()

        current_words: list[str] = []
        current_length = 0

        for word in words:
            additional_length = len(word)

            if current_words:
                additional_length += 1

            if (
                current_words
                and current_length + additional_length > chunk_size
            ):
                parts.append(" ".join(current_words))
                current_words = [word]
                current_length = len(word)
            else:
                current_words.append(word)
                current_length += additional_length

        if current_words:
            parts.append(" ".join(current_words))

        return parts

    @staticmethod
    def _get_overlap_lines(
        lines: list[str],
        overlap: int,
    ) -> list[str]:
        """
        Preserve complete trailing lines for overlap.

        A line is not included when it alone exceeds the overlap target.
        This prevents large duplicate chunks and infinite chunk loops.
        """
        if overlap <= 0:
            return []

        selected: list[str] = []
        selected_length = 0

        for line in reversed(lines):
            line_length = len(line)

            if selected:
                line_length += 1

            if selected_length + line_length > overlap:
                break

            selected.insert(0, line)
            selected_length += line_length

        return selected

    @classmethod
    def chunk_text(
        cls,
        text: str,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> list[str]:
        """
        Divide text into chunks without splitting ordinary lines or words.
        """
        chunk_size = chunk_size or settings.chunk_size

        if overlap is None:
            overlap = settings.chunk_overlap

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if overlap < 0:
            raise ValueError("overlap cannot be negative")

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size"
            )

        if not text or not text.strip():
            return []

        prepared_lines: list[str] = []

        for raw_line in text.strip().splitlines():
            line = raw_line.strip()

            if not line:
                continue

            prepared_lines.extend(
                cls._split_long_line(
                    line=line,
                    chunk_size=chunk_size,
                )
            )

        chunks: list[str] = []
        current_lines: list[str] = []

        for line in prepared_lines:
            candidate_lines = [*current_lines, line]
            candidate_text = "\n".join(candidate_lines)

            if (
                current_lines
                and len(candidate_text) > chunk_size
            ):
                completed_chunk = "\n".join(
                    current_lines
                ).strip()

                if completed_chunk:
                    chunks.append(completed_chunk)

                overlap_lines = cls._get_overlap_lines(
                    lines=current_lines,
                    overlap=overlap,
                )

                # Do not retain overlap when it would prevent the new
                # complete line from fitting inside the next chunk.
                overlap_candidate = "\n".join(
                    [*overlap_lines, line]
                )

                if len(overlap_candidate) > chunk_size:
                    current_lines = []
                else:
                    current_lines = overlap_lines

            current_lines.append(line)

        final_chunk = "\n".join(current_lines).strip()

        if final_chunk:
            chunks.append(final_chunk)

        # Remove accidental consecutive duplicates.
        deduplicated_chunks: list[str] = []

        for chunk in chunks:
            if (
                not deduplicated_chunks
                or deduplicated_chunks[-1] != chunk
            ):
                deduplicated_chunks.append(chunk)

        return deduplicated_chunks

    @classmethod
    def build_chunk_records(
        cls,
        documents: list[Any],
    ) -> list[dict]:
        """
        Convert loaded page documents into records for indexing.
        """
        chunk_records: list[dict] = []

        for document in documents:
            document_id = cls._get_value(
                document,
                "document_id",
            )
            source = cls._get_value(
                document,
                "source",
            )
            page_number = cls._get_value(
                document,
                "page_number",
            )
            text = cls._get_value(
                document,
                "text",
            )

            if not document_id:
                raise ValueError(
                    "Loaded document is missing document_id"
                )

            if not text or not text.strip():
                continue

            chunks = cls.chunk_text(
                text=text,
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap,
            )

            page_token = (
                page_number
                if page_number is not None
                else 0
            )

            for chunk_index, chunk in enumerate(chunks):
                chunk_records.append(
                    {
                        "chunk_id": (
                            f"{document_id}_"
                            f"{page_token}_"
                            f"{chunk_index}"
                        ),
                        "document_id": document_id,
                        "source": source,
                        "page_number": page_number,
                        "chunk_index": chunk_index,
                        "text": chunk,
                    }
                )

        return chunk_records