export function isSpeechSynthesisSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    "speechSynthesis" in window &&
    typeof SpeechSynthesisUtterance !== "undefined"
  );
}

export function prepareTextForSpeech(text: string): string {
  return (
    text
      /*
       * Remove MIRA source-reference
       * markers such as:
       *
       * [Source 1]
       * [source1]
       * [Source 2, Source 3]
       */
      .replace(/\[\s*source\s*\d+(?:\s*,\s*source\s*\d+)*\s*\]/gi, " ")

      /*
       * Remove ordinary Markdown
       * link syntax while preserving
       * the readable link label.
       *
       * [blood pressure](https://...)
       * -> blood pressure
       */
      .replace(/\[([^\]]+)\]\((?:[^)]+)\)/g, "$1")

      /*
       * Remove inline code markers.
       */
      .replace(/`([^`]+)`/g, "$1")

      /*
       * Remove Markdown emphasis
       * characters so browsers do not
       * pronounce "asterisk".
       */
      .replace(/[*_~]+/g, "")

      /*
       * Remove heading/list markup that
       * should not be spoken literally.
       */
      .replace(/^\s*#{1,6}\s+/gm, "")
      .replace(/^\s*[-+]\s+/gm, "")
      /*
       * Remove Markdown table separator rows:
       *
       * |---|---|
       * |:---|---:|
       */
      .replace(/^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$/gm, " ")

      /*
       * Convert Markdown table cells into
       * natural spoken pauses.
       *
       * | A | B | C |
       * -> A. B. C.
       */
      .replace(/^\s*\|(.+)\|\s*$/gm, (_match, row: string) => {
        return (
          row
            .split("|")
            .map((cell) => cell.trim())
            .filter(Boolean)
            .join(". ") + "."
        );
      })
      /*
       * Normalize numeric ranges for speech.
       *
       * 13.5–17.5
       * -> 13.5 to 17.5
       */
      .replace(/(\d)\s*[–—-]\s*(\d)/g, "$1 to $2")

      /*
       * Expand common medical unit formatting.
       */
      .replace(/\bg\s*\/\s*dL\b/gi, "grams per deciliter")
      .replace(/\bmg\s*\/\s*dL\b/gi, "milligrams per deciliter")
      .replace(/\bmmHg\b/gi, "millimeters of mercury")

      /*
       * Replace any remaining pipe characters
       * defensively so TTS never says
       * "vertical bar".
       */
      .replace(/\|+/g, ". ")
      /*
       * Convert repeated whitespace and
       * newlines into natural pauses.
       */
      .replace(/\s+/g, " ")
      .trim()
  );
}

export function createSpeechUtterance(
  text: string,
): SpeechSynthesisUtterance | null {
  if (!isSpeechSynthesisSupported()) {
    return null;
  }

  const cleanedText = prepareTextForSpeech(text);

  if (!cleanedText) {
    return null;
  }

  const utterance = new SpeechSynthesisUtterance(cleanedText);

  utterance.lang = navigator.language || "en-US";

  utterance.rate = 1;
  utterance.pitch = 1;
  utterance.volume = 1;

  return utterance;
}
