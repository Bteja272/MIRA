import type {
  DocumentSummary,
} from "../types/documents";

interface DocumentSelectorProps {
  documents: DocumentSummary[];
  selectedIds: string[];
  maximumSelected: number;
  disabled?: boolean;
  onChange: (selectedIds: string[]) => void;
}

function formatDocumentType(
  value: string | null,
): string {
  if (!value) {
    return "Unclassified";
  }

  return value
    .split("_")
    .map(
      (part) =>
        part.charAt(0).toUpperCase()
        + part.slice(1),
    )
    .join(" ");
}

export function DocumentSelector({
  documents,
  selectedIds,
  maximumSelected,
  disabled = false,
  onChange,
}: DocumentSelectorProps) {
  function toggleDocument(
    documentId: string,
  ): void {
    if (selectedIds.includes(documentId)) {
      onChange(
        selectedIds.filter(
          (selectedId) => selectedId !== documentId,
        ),
      );
      return;
    }

    if (selectedIds.length >= maximumSelected) {
      return;
    }

    onChange([...selectedIds, documentId]);
  }

  if (documents.length === 0) {
    return (
      <div className="selector-empty">
        No uploaded documents are available. You can still ask a general
        educational question without selecting a document.
      </div>
    );
  }

  return (
    <div className="document-selector">
      {documents.map((document) => {
        const isSelected = selectedIds.includes(document.document_id);
        const selectionLimitReached =
          selectedIds.length >= maximumSelected && !isSelected;

        return (
          <label
            className={
              isSelected
                ? "document-option document-option--selected"
                : "document-option"
            }
            key={document.document_id}
          >
            <input
              type="checkbox"
              checked={isSelected}
              disabled={disabled || selectionLimitReached}
              onChange={() => toggleDocument(document.document_id)}
            />

            <span className="document-option__content">
              <strong title={document.filename}>
                {document.filename}
              </strong>
              <span>
                {formatDocumentType(document.document_type)} · {document.chunk_count}
                {document.chunk_count === 1 ? " chunk" : " chunks"}
              </span>
            </span>
          </label>
        );
      })}
    </div>
  );
}