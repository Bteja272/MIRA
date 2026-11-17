import {
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  deleteDocument,
  getDocuments,
  uploadDocument,
} from "../api/documents";
import { ApiError } from "../api/http";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { StatusBanner } from "../components/StatusBanner";
import type {
  DocumentSummary,
  IngestResponse,
  UploadProgress,
} from "../types/documents";
import "../styles/documents.css";

const MAX_FILE_BYTES = 25 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".pdf", ".txt"];

function formatBytes(value: number | null): string {
  if (value === null || value < 0) {
    return "Unknown";
  }

  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatUploadedAt(value: string | null): string {
  if (!value) {
    return "Unknown";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
  }).format(date);
}

function formatDocumentType(value: string | null): string {
  if (!value) {
    return "Unclassified";
  }

  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getExtension(filename: string): string {
  const segments = filename.split(".");
  const extension = segments.length > 1 ? segments.at(-1) : null;
  return extension ? extension.toUpperCase() : "FILE";
}

function validateFile(file: File): string | null {
  const lowerName = file.name.toLowerCase();
  const hasAllowedExtension = ALLOWED_EXTENSIONS.some(
    (extension) => lowerName.endsWith(extension),
  );

  if (!hasAllowedExtension) {
    return "Only PDF and TXT files are allowed.";
  }

  if (file.size === 0) {
    return "The selected file is empty.";
  }

  if (file.size > MAX_FILE_BYTES) {
    return "The selected file exceeds the 25 MB limit.";
  }

  return null;
}

function FileIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M6 3.75h7.1L18 8.65v11.6H6z" />
      <path d="M13 3.75v5h5" />
      <path d="M9 13h6M9 16.5h4.5" />
    </svg>
  );
}

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFileError, setSelectedFileError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [uploadResult, setUploadResult] = useState<IngestResponse | null>(null);
  const [documentToDelete, setDocumentToDelete] = useState<DocumentSummary | null>(null);

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(file, setUploadProgress),
    onMutate: () => {
      setUploadResult(null);
      setUploadProgress({ loaded: 0, total: 0, percentage: 0 });
    },
    onSuccess: async (result) => {
      setUploadResult(result);
      setSelectedFile(null);
      setSelectedFileError(null);
      setUploadProgress({ loaded: 1, total: 1, percentage: 100 });

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      await queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: () => {
      setUploadProgress(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (documentId: string) => deleteDocument(documentId),
    onSuccess: async () => {
      setDocumentToDelete(null);
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  function handleFileChange(event: ChangeEvent<HTMLInputElement>): void {
    const file = event.target.files?.[0] ?? null;

    setUploadResult(null);
    uploadMutation.reset();

    if (!file) {
      setSelectedFile(null);
      setSelectedFileError(null);
      return;
    }

    const validationError = validateFile(file);

    if (validationError) {
      setSelectedFile(null);
      setSelectedFileError(validationError);
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
    setSelectedFileError(null);
  }

  function handleUpload(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();

    if (!selectedFile) {
      setSelectedFileError("Select a PDF or TXT file first.");
      return;
    }

    uploadMutation.mutate(selectedFile);
  }

  const uploadError =
    uploadMutation.error instanceof ApiError
      ? uploadMutation.error.message
      : uploadMutation.isError
        ? "The document could not be uploaded."
        : null;

  const deleteError =
    deleteMutation.error instanceof ApiError
      ? deleteMutation.error.message
      : deleteMutation.isError
        ? "The document could not be deleted."
        : null;

  const documents = documentsQuery.data?.documents ?? [];

  return (
    <section className="page-stack documents-page">
      <header className="page-header documents-page__header">
        <div>
          <p className="eyebrow">Documents</p>
          <h2>Medical documents</h2>
          <p>Upload and manage the medical records available to MIRA.</p>
        </div>

        <span className="connection-badge">
          {documents.length} document{documents.length === 1 ? "" : "s"}
        </span>
      </header>

      <section className="upload-panel" aria-labelledby="upload-document-title">
        <div className="upload-panel__copy">
          <div className="upload-panel__icon" aria-hidden="true">
            <FileIcon />
          </div>
          <div>
            <h3 id="upload-document-title">Upload document</h3>
            <p>PDF or TXT · maximum 25 MB</p>
          </div>
        </div>

        <form className="upload-form" onSubmit={handleUpload}>
          <div className="file-picker-row">
            <label className="file-picker" htmlFor="medical-document">
              <span className="file-picker__action">
                {selectedFile ? "Change file" : "Choose file"}
              </span>
              <input
                id="medical-document"
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,application/pdf,text/plain"
                disabled={uploadMutation.isPending}
                onChange={handleFileChange}
              />
            </label>

            <div className="file-picker__selection" aria-live="polite">
              {selectedFile ? (
                <>
                  <strong>{selectedFile.name}</strong>
                  <span>{formatBytes(selectedFile.size)}</span>
                </>
              ) : (
                <span>No file selected</span>
              )}
            </div>

            <button
              className="button button--primary upload-form__submit"
              type="submit"
              disabled={!selectedFile || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? "Processing…" : "Upload document"}
            </button>
          </div>

          {selectedFileError && (
            <StatusBanner tone="error">{selectedFileError}</StatusBanner>
          )}

          {uploadError && <StatusBanner tone="error">{uploadError}</StatusBanner>}

          {uploadResult && (
            <StatusBanner tone={uploadResult.duplicate ? "info" : "success"}>
              {uploadResult.message}
              {uploadResult.duplicate && uploadResult.existing_document_id && (
                <>
                  {" "}Existing document ID:{" "}
                  <code>{uploadResult.existing_document_id}</code>
                </>
              )}
            </StatusBanner>
          )}

          {uploadMutation.isPending && uploadProgress && (
            <div className="upload-progress" role="status" aria-live="polite">
              <div className="upload-progress__header">
                <span>Uploading and indexing…</span>
                <strong>{uploadProgress.percentage}%</strong>
              </div>
              <progress max={100} value={uploadProgress.percentage} />
            </div>
          )}
        </form>
      </section>

      <section className="document-section" aria-labelledby="documents-list-title">
        <div className="section-heading">
          <div>
            <h3 id="documents-list-title">Your documents</h3>
            <p>Records currently indexed for your account.</p>
          </div>

          <button
            className="button button--secondary"
            type="button"
            disabled={documentsQuery.isFetching}
            onClick={() => {
              void documentsQuery.refetch();
            }}
          >
            {documentsQuery.isFetching ? "Refreshing…" : "Refresh"}
          </button>
        </div>

        {documentsQuery.isLoading && (
          <div className="document-state" role="status">
            Loading documents…
          </div>
        )}

        {documentsQuery.isError && (
          <StatusBanner tone="error">
            {documentsQuery.error instanceof ApiError
              ? documentsQuery.error.message
              : "The document list could not be loaded."}
          </StatusBanner>
        )}

        {deleteError && <StatusBanner tone="error">{deleteError}</StatusBanner>}

        {!documentsQuery.isLoading &&
          !documentsQuery.isError &&
          documents.length === 0 && (
            <div className="document-state document-state--empty">
              <div className="document-state__icon" aria-hidden="true">
                <FileIcon />
              </div>
              <h4>No documents yet</h4>
              <p>Upload a synthetic PDF or TXT file to begin using MIRA.</p>
            </div>
          )}

        {documents.length > 0 && (
          <div className="document-list">
            {documents.map((document) => (
              <article className="document-row" key={document.document_id}>
                <div className="document-row__icon" aria-hidden="true">
                  <FileIcon />
                </div>

                <div className="document-row__main">
                  <div className="document-row__title-line">
                    <h4 title={document.filename}>{document.filename}</h4>
                    <span className="document-type">
                      {formatDocumentType(document.document_type)}
                    </span>
                  </div>

                  <div className="document-row__meta">
                    <span>{getExtension(document.filename)}</span>
                    <span aria-hidden="true">·</span>
                    <span>{formatBytes(document.file_size_bytes)}</span>
                    <span aria-hidden="true">·</span>
                    <span>{document.chunk_count} chunks</span>
                    <span aria-hidden="true">·</span>
                    <span>Uploaded {formatUploadedAt(document.uploaded_at)}</span>
                  </div>
                </div>

                <button
                  className="document-row__delete"
                  type="button"
                  aria-label={`Delete ${document.filename}`}
                  onClick={() => {
                    deleteMutation.reset();
                    setDocumentToDelete(document);
                  }}
                >
                  Delete
                </button>
              </article>
            ))}
          </div>
        )}
      </section>

      <ConfirmDialog
        isOpen={documentToDelete !== null}
        title="Delete this document?"
        description={
          documentToDelete
            ? `"${documentToDelete.filename}" and its chunks, embeddings, stored extraction, and physical file will be permanently deleted.`
            : ""
        }
        confirmLabel="Delete permanently"
        isConfirming={deleteMutation.isPending}
        onCancel={() => {
          if (!deleteMutation.isPending) {
            setDocumentToDelete(null);
          }
        }}
        onConfirm={() => {
          if (documentToDelete) {
            deleteMutation.mutate(documentToDelete.document_id);
          }
        }}
      />
    </section>
  );
}
