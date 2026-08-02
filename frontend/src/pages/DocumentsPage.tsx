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

const MAX_FILE_BYTES =
  25 * 1024 * 1024;

const ALLOWED_EXTENSIONS = [
  ".pdf",
  ".txt",
];

function formatBytes(
  value: number | null,
): string {
  if (
    value === null ||
    value < 0
  ) {
    return "Unknown";
  }

  if (value < 1024) {
    return `${value} B`;
  }

  if (
    value < 1024 * 1024
  ) {
    return (
      `${(value / 1024).toFixed(1)} KB`
    );
  }

  return (
    `${(
      value /
      (1024 * 1024)
    ).toFixed(1)} MB`
  );
}

function formatUploadedAt(
  value: string | null,
): string {
  if (!value) {
    return "Unknown";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
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

function validateFile(
  file: File,
): string | null {
  const lowerName =
    file.name.toLowerCase();

  const hasAllowedExtension =
    ALLOWED_EXTENSIONS.some(
      (extension) =>
        lowerName.endsWith(
          extension,
        ),
    );

  if (!hasAllowedExtension) {
    return (
      "Only PDF and TXT files are allowed."
    );
  }

  if (file.size === 0) {
    return (
      "The selected file is empty."
    );
  }

  if (
    file.size > MAX_FILE_BYTES
  ) {
    return (
      "The selected file exceeds "
      + "the 25 MB limit."
    );
  }

  return null;
}

export function DocumentsPage() {
  const queryClient =
    useQueryClient();

  const fileInputRef =
    useRef<HTMLInputElement>(null);

  const [
    selectedFile,
    setSelectedFile,
  ] = useState<File | null>(
    null,
  );

  const [
    selectedFileError,
    setSelectedFileError,
  ] = useState<string | null>(
    null,
  );

  const [
    uploadProgress,
    setUploadProgress,
  ] = useState<UploadProgress | null>(
    null,
  );

  const [
    uploadResult,
    setUploadResult,
  ] = useState<IngestResponse | null>(
    null,
  );

  const [
    documentToDelete,
    setDocumentToDelete,
  ] = useState<DocumentSummary | null>(
    null,
  );

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
  });

  const uploadMutation = useMutation({
    mutationFn: (
      file: File,
    ) => uploadDocument(
      file,
      setUploadProgress,
    ),
    onMutate: () => {
      setUploadResult(null);
      setUploadProgress({
        loaded: 0,
        total: 0,
        percentage: 0,
      });
    },
    onSuccess: async (
      result,
    ) => {
      setUploadResult(result);
      setSelectedFile(null);
      setSelectedFileError(null);
      setUploadProgress({
        loaded: 1,
        total: 1,
        percentage: 100,
      });

      if (
        fileInputRef.current
      ) {
        fileInputRef.current.value = "";
      }

      await queryClient.invalidateQueries({
        queryKey: ["documents"],
      });
    },
    onError: () => {
      setUploadProgress(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (
      documentId: string,
    ) => deleteDocument(
      documentId,
    ),
    onSuccess: async () => {
      setDocumentToDelete(null);

      await queryClient.invalidateQueries({
        queryKey: ["documents"],
      });
    },
  });

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ): void {
    const file =
      event.target.files?.[0]
      ?? null;

    setUploadResult(null);
    uploadMutation.reset();

    if (!file) {
      setSelectedFile(null);
      setSelectedFileError(null);
      return;
    }

    const validationError =
      validateFile(file);

    if (validationError) {
      setSelectedFile(null);
      setSelectedFileError(
        validationError,
      );

      event.target.value = "";
      return;
    }

    setSelectedFile(file);
    setSelectedFileError(null);
  }

  function handleUpload(
    event: FormEvent<HTMLFormElement>,
  ): void {
    event.preventDefault();

    if (!selectedFile) {
      setSelectedFileError(
        "Select a PDF or TXT file first.",
      );
      return;
    }

    uploadMutation.mutate(
      selectedFile,
    );
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

  const documents =
    documentsQuery.data?.documents
    ?? [];

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Document workspace
          </p>

          <h2>Medical documents</h2>

          <p>
            Upload synthetic PDF or TXT documents,
            review indexed metadata, and permanently
            delete owned records.
          </p>
        </div>

        <span className="connection-badge">
          {documents.length} document
          {documents.length === 1
            ? ""
            : "s"}
        </span>
      </header>

      <section className="upload-panel">
        <div className="upload-panel__copy">
          <p className="eyebrow">
            Add a document
          </p>

          <h3>Upload and index</h3>

          <p>
            Files are limited to PDF or TXT and
            25 MB. MIRA extracts readable text,
            classifies the document, creates chunks,
            generates embeddings, and stores the
            indexed result under your account.
          </p>
        </div>

        <form
          className="upload-form"
          onSubmit={handleUpload}
        >
          <label
            className="file-picker"
            htmlFor="medical-document"
          >
            <span className="file-picker__title">
              Choose a PDF or TXT file
            </span>

            <span className="file-picker__details">
              {selectedFile
                ? (
                  selectedFile.name
                  + " · "
                  + formatBytes(
                    selectedFile.size,
                  )
                )
                : "No file selected"}
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

          {selectedFileError && (
            <StatusBanner tone="error">
              {selectedFileError}
            </StatusBanner>
          )}

          {uploadError && (
            <StatusBanner tone="error">
              {uploadError}
            </StatusBanner>
          )}

          {uploadResult && (
            <StatusBanner
              tone={
                uploadResult.duplicate
                  ? "info"
                  : "success"
              }
            >
              {uploadResult.message}
              {uploadResult.duplicate &&
                uploadResult
                  .existing_document_id && (
                  <>
                    {" "}
                    Existing document ID:{" "}
                    <code>
                      {
                        uploadResult
                          .existing_document_id
                      }
                    </code>
                  </>
                )}
            </StatusBanner>
          )}

          {uploadMutation.isPending &&
            uploadProgress && (
              <div
                className="upload-progress"
                role="status"
                aria-live="polite"
              >
                <div className="upload-progress__header">
                  <span>
                    Uploading and indexing…
                  </span>
                  <strong>
                    {
                      uploadProgress
                        .percentage
                    }
                    %
                  </strong>
                </div>

                <progress
                  max={100}
                  value={
                    uploadProgress
                      .percentage
                  }
                />
              </div>
            )}

          <button
            className="button button--primary"
            type="submit"
            disabled={
              !selectedFile ||
              uploadMutation.isPending
            }
          >
            {uploadMutation.isPending
              ? "Processing document…"
              : "Upload document"}
          </button>
        </form>
      </section>

      <section className="document-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">
              Indexed records
            </p>

            <h3>Your documents</h3>
          </div>

          <button
            className="button button--secondary"
            type="button"
            disabled={
              documentsQuery.isFetching
            }
            onClick={() => {
              void documentsQuery.refetch();
            }}
          >
            {documentsQuery.isFetching
              ? "Refreshing…"
              : "Refresh"}
          </button>
        </div>

        {documentsQuery.isLoading && (
          <div
            className="document-state"
            role="status"
          >
            Loading documents…
          </div>
        )}

        {documentsQuery.isError && (
          <StatusBanner tone="error">
            {documentsQuery.error
              instanceof ApiError
              ? (
                documentsQuery
                  .error
                  .message
              )
              : (
                "The document list "
                + "could not be loaded."
              )}
          </StatusBanner>
        )}

        {deleteError && (
          <StatusBanner tone="error">
            {deleteError}
          </StatusBanner>
        )}

        {!documentsQuery.isLoading &&
          !documentsQuery.isError &&
          documents.length === 0 && (
            <div className="document-state">
              <h4>No documents yet</h4>
              <p>
                Upload a synthetic PDF or TXT file
                to begin using MIRA.
              </p>
            </div>
          )}

        {documents.length > 0 && (
          <div className="document-grid">
            {documents.map(
              (document) => (
                <article
                  className="document-card"
                  key={
                    document.document_id
                  }
                >
                  <div className="document-card__header">
                    <span className="document-type">
                      {formatDocumentType(
                        document.document_type,
                      )}
                    </span>

                    <button
                      className="icon-button icon-button--danger"
                      type="button"
                      aria-label={
                        "Delete "
                        + document.filename
                      }
                      onClick={() => {
                        deleteMutation.reset();
                        setDocumentToDelete(
                          document,
                        );
                      }}
                    >
                      Delete
                    </button>
                  </div>

                  <div>
                    <h4 title={document.filename}>
                      {document.filename}
                    </h4>

                    <code className="document-id">
                      {
                        document.document_id
                      }
                    </code>
                  </div>

                  <dl className="document-metadata">
                    <div>
                      <dt>Size</dt>
                      <dd>
                        {formatBytes(
                          document
                            .file_size_bytes,
                        )}
                      </dd>
                    </div>

                    <div>
                      <dt>Chunks</dt>
                      <dd>
                        {
                          document
                            .chunk_count
                        }
                      </dd>
                    </div>

                    <div>
                      <dt>Uploaded</dt>
                      <dd>
                        {formatUploadedAt(
                          document
                            .uploaded_at,
                        )}
                      </dd>
                    </div>
                  </dl>
                </article>
              ),
            )}
          </div>
        )}
      </section>

      <ConfirmDialog
        isOpen={
          documentToDelete !== null
        }
        title="Delete this document?"
        description={
          documentToDelete
            ? (
              `"${documentToDelete.filename}" `
              + "and its chunks, embeddings, "
              + "stored extraction, and physical "
              + "file will be permanently deleted."
            )
            : ""
        }
        confirmLabel="Delete permanently"
        isConfirming={
          deleteMutation.isPending
        }
        onCancel={() => {
          if (
            !deleteMutation.isPending
          ) {
            setDocumentToDelete(
              null,
            );
          }
        }}
        onConfirm={() => {
          if (
            documentToDelete
          ) {
            deleteMutation.mutate(
              documentToDelete
                .document_id,
            );
          }
        }}
      />
    </section>
  );
}