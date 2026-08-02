import type {
  QuerySource,
} from "../types/query";

interface SourceCardProps {
  source: QuerySource;
  index: number;
}

function stringValue(
  source: QuerySource,
  keys: string[],
): string | null {
  for (const key of keys) {
    const value = source[key];

    if (
      typeof value === "string"
      && value.trim()
    ) {
      return value.trim();
    }
  }

  return null;
}

function numberValue(
  source: QuerySource,
  keys: string[],
): number | null {
  for (const key of keys) {
    const value = source[key];

    if (
      typeof value === "number"
      && Number.isFinite(value)
    ) {
      return value;
    }

    if (
      typeof value === "string"
      && value.trim()
      && Number.isFinite(
        Number(value),
      )
    ) {
      return Number(value);
    }
  }

  return null;
}

function safeExternalUrl(
  value: string | null,
): string | null {
  if (!value) {
    return null;
  }

  try {
    const parsedUrl = new URL(value);

    if (
      parsedUrl.protocol !== "http:"
      && parsedUrl.protocol !== "https:"
    ) {
      return null;
    }

    return parsedUrl.toString();
  } catch {
    return null;
  }
}

export function SourceCard({
  source,
  index,
}: SourceCardProps) {
  const title = stringValue(
    source,
    [
      "title",
      "source_filename",
      "filename",
      "source",
      "document_name",
    ],
  );

  const rawUrl = stringValue(
    source,
    [
      "url",
      "source_url",
    ],
  );

  const sourceUrl = safeExternalUrl(
    rawUrl,
  );

  const quotedText = stringValue(
    source,
    [
      "quoted_text",
      "content",
      "text",
      "chunk_text",
    ],
  );

  const sourceNumber = numberValue(
    source,
    [
      "source_number",
    ],
  );

  const pageNumber = numberValue(
    source,
    [
      "page_number",
      "page",
    ],
  );

  const chunkIndex = numberValue(
    source,
    [
      "chunk_index",
      "index",
    ],
  );

  const documentId = stringValue(
    source,
    [
      "document_id",
    ],
  );

  const chunkId = stringValue(
    source,
    [
      "chunk_id",
    ],
  );

  const isWebSource =
    sourceUrl !== null
    || sourceNumber !== null;

  const labelNumber =
    sourceNumber
    ?? index + 1;

  return (
    <article className="source-card">
      <header className="source-card__header">
        <span className="source-label">
          {isWebSource
            ? `Web Source ${labelNumber}`
            : `Source ${labelNumber}`}
        </span>

        {sourceUrl ? (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noreferrer noopener"
          >
            {title ?? "Web source"}
          </a>
        ) : (
          <strong>
            {title ?? "Document source"}
          </strong>
        )}
      </header>

      <dl className="source-metadata">
        {pageNumber !== null && (
          <div>
            <dt>Page</dt>
            <dd>{pageNumber}</dd>
          </div>
        )}

        {chunkIndex !== null && (
          <div>
            <dt>Chunk</dt>
            <dd>{chunkIndex}</dd>
          </div>
        )}

        {documentId && (
          <div>
            <dt>Document ID</dt>
            <dd title={documentId}>
              {documentId}
            </dd>
          </div>
        )}

        {chunkId && (
          <div>
            <dt>Chunk ID</dt>
            <dd title={chunkId}>
              {chunkId}
            </dd>
          </div>
        )}

        {sourceUrl && (
          <div>
            <dt>Website</dt>
            <dd title={sourceUrl}>
              {new URL(
                sourceUrl,
              ).hostname}
            </dd>
          </div>
        )}
      </dl>

      {quotedText && (
        <blockquote>
          {quotedText}
        </blockquote>
      )}
    </article>
  );
}