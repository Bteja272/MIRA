import {
  EvidenceDetails,
} from "./EvidenceDetails";
import type {
  ExtractionMethod,
  SourceEvidence,
} from "../types/extractions";

export interface ExtractionFactDetail {
  label: string;
  value: string | number | null;
}

interface ExtractionFactCardProps {
  title: string;
  details?: ExtractionFactDetail[];
  confidence: number;
  extractionMethod: ExtractionMethod;
  sources: SourceEvidence[];
  status?: string | null;
}

function humanize(
  value: string,
): string {
  return value
    .split("_")
    .map(
      (part) =>
        part.charAt(0).toUpperCase()
        + part.slice(1),
    )
    .join(" ");
}

function confidenceLabel(
  confidence: number,
): string {
  return `${Math.round(confidence * 100)}%`;
}

export function ExtractionFactCard({
  title,
  details = [],
  confidence,
  extractionMethod,
  sources,
  status = null,
}: ExtractionFactCardProps) {
  const visibleDetails =
    details.filter(
      (detail) =>
        detail.value !== null
        && detail.value !== "",
    );

  return (
    <article className="extraction-fact-card">
      <header className="extraction-fact-card__header">
        <h4>{title}</h4>

        <div className="fact-badges">
          {status && (
            <span className="fact-badge">
              {humanize(status)}
            </span>
          )}

          <span className="fact-badge">
            {humanize(extractionMethod)}
          </span>

          <span className="fact-badge fact-badge--confidence">
            {confidenceLabel(confidence)}
          </span>
        </div>
      </header>

      {visibleDetails.length > 0 && (
        <dl className="fact-details">
          {visibleDetails.map(
            (detail) => (
              <div key={detail.label}>
                <dt>{detail.label}</dt>
                <dd>{detail.value}</dd>
              </div>
            ),
          )}
        </dl>
      )}

      <EvidenceDetails sources={sources} />
    </article>
  );
}