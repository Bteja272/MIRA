import re


class TextCleanerService:
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Normalize extracted text while preserving line boundaries.

        Medical documents often place a test name, result, reference range,
        and flag on separate lines. Removing those boundaries can cause the
        LLM to associate values with the wrong test.
        """
        if not text:
            return ""

        text = text.replace("\r\n", "\n").replace("\r", "\n")

        cleaned_lines: list[str] = []

        for line in text.split("\n"):
            # Collapse repeated spaces and tabs inside a line.
            cleaned_line = re.sub(r"[ \t]+", " ", line).strip()

            if cleaned_line:
                cleaned_lines.append(cleaned_line)

        return "\n".join(cleaned_lines)