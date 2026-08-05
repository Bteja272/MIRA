import type {
  SourceEvidence,
} from "../types/extractions";

interface EvidenceDetailsProps {
  sources: SourceEvidence[];
}

export function EvidenceDetails({
  sources,
}: EvidenceDetailsProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <details className="evidence-details">
      <summary>
        View {sources.length} evidence source
        {sources.length === 1 ? "" : "s"}
      </summary>

      <div className="evidence-list">
        {sources.map(
          (source, index) => (
            <article
              className="evidence-item"
              key={`${source.chunk_id}-${index}`}
            >
              <div className="evidence-item__metadata">
                <strong>
                  {source.source_filename
                    ?? "Document source"}
                </strong>

                <span>
                  Chunk {source.chunk_index}
                  {source.page_number !== null
                    ? ` · Page ${source.page_number}`
                    : ""}
                </span>
              </div>

              <blockquote>
                {source.quoted_text}
              </blockquote>
            </article>
          ),
        )}
      </div>
    </details>
  );
}