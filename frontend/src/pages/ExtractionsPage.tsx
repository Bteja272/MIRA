import {
  useEffect,
  useState,
} from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getDocuments,
} from "../api/documents";
import {
  deleteExtraction,
  generateExtraction,
  getExtractionOrNull,
} from "../api/extractions";
import {
  ApiError,
} from "../api/http";
import {
  ConfirmDialog,
} from "../components/ConfirmDialog";
import {
  ExtractionFactCard,
} from "../components/ExtractionFactCard";
import {
  StatusBanner,
} from "../components/StatusBanner";
import type {
  SourceEvidence,
  SourcedDateValue,
  SourcedTextValue,
} from "../types/extractions";
import "../styles/extractions.css";

type PatientFact =
  | {
      title: string;
      value: SourcedTextValue;
      date: false;
    }
  | {
      title: string;
      value: SourcedDateValue;
      date: true;
    };

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

function formatDateTime(
  value: string,
): string {
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

function confidencePercent(
  value: number,
): string {
  return `${Math.round(value * 100)}%`;
}

function mergeSources(
  ...groups: (
    SourceEvidence[] | undefined
  )[]
): SourceEvidence[] {
  const merged =
    groups.flatMap(
      (group) => group ?? [],
    );

  const unique = new Map<
    string,
    SourceEvidence
  >();

  for (const source of merged) {
    const key = [
      source.document_id,
      source.chunk_id,
      source.chunk_index,
      source.quoted_text,
    ].join(":");

    if (!unique.has(key)) {
      unique.set(key, source);
    }
  }

  return [...unique.values()];
}

function sourcedTextDetails(
  value: SourcedTextValue,
) {
  return [
    {
      label: "Value",
      value: value.value,
    },
  ];
}

function sourcedDateDetails(
  value: SourcedDateValue,
) {
  return [
    {
      label: "Document text",
      value: value.raw_value,
    },
    {
      label: "Normalized date",
      value:
        value.normalized_value
        ?? "Not normalized",
    },
  ];
}

function elapsedMessage(
  seconds: number,
): string {
  if (seconds < 15) {
    return (
      "Loading document context and "
      + "preparing extraction…"
    );
  }

  if (seconds < 45) {
    return (
      "The local model is identifying "
      + "medical facts and evidence…"
    );
  }

  return (
    "The local model is still processing. "
    + "Structured extraction may take "
    + "more than one minute."
  );
}

export function ExtractionsPage() {
  const queryClient =
    useQueryClient();

  const [
    selectedDocumentId,
    setSelectedDocumentId,
  ] = useState("");

  const [
    generationMessage,
    setGenerationMessage,
  ] = useState<string | null>(
    null,
  );

  const [
    elapsedSeconds,
    setElapsedSeconds,
  ] = useState(0);

  const [
    regenerateDialogOpen,
    setRegenerateDialogOpen,
  ] = useState(false);

  const [
    deleteDialogOpen,
    setDeleteDialogOpen,
  ] = useState(false);

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
  });

  const extractionQuery = useQuery({
    queryKey: [
      "extraction",
      selectedDocumentId,
    ],
    queryFn: () =>
      getExtractionOrNull(
        selectedDocumentId,
      ),
    enabled:
      selectedDocumentId.length > 0,
  });

  const generateMutation = useMutation({
    mutationFn: ({
      documentId,
      replaceExisting,
    }: {
      documentId: string;
      replaceExisting: boolean;
    }) =>
      generateExtraction(
        documentId,
        replaceExisting,
      ),
    onMutate: () => {
      setGenerationMessage(null);
      setElapsedSeconds(0);
    },
    onSuccess: (
      response,
    ) => {
      queryClient.setQueryData(
        [
          "extraction",
          response.result.document_id,
        ],
        response.result,
      );

      setGenerationMessage(
        response.message,
      );

      setRegenerateDialogOpen(
        false,
      );
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (
      documentId: string,
    ) => deleteExtraction(
      documentId,
    ),
    onSuccess: (
      response,
    ) => {
      queryClient.setQueryData(
        [
          "extraction",
          response.document_id,
        ],
        null,
      );

      setGenerationMessage(
        response.message,
      );

      setDeleteDialogOpen(false);
    },
  });

  useEffect(() => {
    if (!generateMutation.isPending) {
      return;
    }

    const intervalId =
      window.setInterval(
        () => {
          setElapsedSeconds(
            (current) =>
              current + 1,
          );
        },
        1000,
      );

    return () => {
      window.clearInterval(
        intervalId,
      );
    };
  }, [
    generateMutation.isPending,
  ]);

  const documents =
    documentsQuery.data?.documents
    ?? [];

  const selectedDocument =
    documents.find(
      (document) =>
        document.document_id
        === selectedDocumentId,
    ) ?? null;

  const persistedExtraction =
    extractionQuery.data ?? null;

  const extraction =
    persistedExtraction?.extraction
    ?? null;

  const generateError =
    generateMutation.error
      instanceof ApiError
      ? generateMutation.error.message
      : generateMutation.isError
        ? (
          "The structured extraction "
          + "could not be generated."
        )
        : null;

  const deleteError =
    deleteMutation.error
      instanceof ApiError
      ? deleteMutation.error.message
      : deleteMutation.isError
        ? (
          "The structured extraction "
          + "could not be deleted."
        )
        : null;

  const extractionLoadError =
    extractionQuery.error
      instanceof ApiError
      ? extractionQuery.error.message
      : extractionQuery.isError
        ? (
          "The stored extraction "
          + "could not be loaded."
        )
        : null;

  const patientFacts: PatientFact[] = [];

  if (extraction?.patient.name) {
    patientFacts.push({
      title: "Patient name",
      value: extraction.patient.name,
      date: false,
    });
  }

  if (extraction?.patient.date_of_birth) {
    patientFacts.push({
      title: "Date of birth",
      value: extraction.patient.date_of_birth,
      date: true,
    });
  }

  if (
    extraction?.patient
      .medical_record_number
  ) {
    patientFacts.push({
      title: "Medical record number",
      value:
        extraction.patient
          .medical_record_number,
      date: false,
    });
  }

  if (extraction?.document_date) {
    patientFacts.push({
      title: "Document date",
      value: extraction.document_date,
      date: true,
    });
  }

  function generate(
    replaceExisting: boolean,
  ): void {
    if (!selectedDocumentId) {
      return;
    }

    generateMutation.mutate({
      documentId:
        selectedDocumentId,
      replaceExisting,
    });
  }

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Structured medical data
          </p>

          <h2>
            Medical extraction
          </h2>

          <p>
            Generate a validated, evidence-backed
            structured view of one owned medical
            document.
          </p>
        </div>

        {extraction && (
          <span className="connection-badge">
            {confidencePercent(
              extraction
                .extraction_confidence,
            )}
            {" confidence"}
          </span>
        )}
      </header>

      <section className="extraction-control-panel">
        <label
          className="field"
          htmlFor="extraction-document"
        >
          <span>Select a document</span>

          <select
            id="extraction-document"
            value={selectedDocumentId}
            disabled={
              documentsQuery.isLoading
              || generateMutation.isPending
              || deleteMutation.isPending
            }
            onChange={(event) => {
              setSelectedDocumentId(
                event.target.value,
              );
              setGenerationMessage(null);
              generateMutation.reset();
              deleteMutation.reset();
            }}
          >
            <option value="">
              Choose an uploaded document
            </option>

            {documents.map(
              (document) => (
                <option
                  key={
                    document.document_id
                  }
                  value={
                    document.document_id
                  }
                >
                  {document.filename}
                  {" · "}
                  {humanize(
                    document.document_type
                    ?? "unknown",
                  )}
                </option>
              ),
            )}
          </select>
        </label>

        {documentsQuery.isError && (
          <StatusBanner tone="error">
            {documentsQuery.error
              instanceof ApiError
              ? documentsQuery.error.message
              : (
                "The document list "
                + "could not be loaded."
              )}
          </StatusBanner>
        )}

        {selectedDocument && (
          <div className="selected-document-summary">
            <div>
              <strong>
                {selectedDocument.filename}
              </strong>

              <span>
                {humanize(
                  selectedDocument.document_type
                  ?? "unknown",
                )}
                {" · "}
                {
                  selectedDocument
                    .chunk_count
                }
                {" chunk"}
                {selectedDocument.chunk_count
                  === 1
                  ? ""
                  : "s"}
              </span>
            </div>

            <code>
              {
                selectedDocument
                  .document_id
              }
            </code>
          </div>
        )}

        <div className="extraction-actions">
          {!persistedExtraction ? (
            <button
              className="button button--primary"
              type="button"
              disabled={
                !selectedDocumentId
                || generateMutation.isPending
                || extractionQuery.isLoading
              }
              onClick={() =>
                generate(false)
              }
            >
              {generateMutation.isPending
                ? "Generating extraction…"
                : "Generate extraction"}
            </button>
          ) : (
            <>
              <button
                className="button button--secondary"
                type="button"
                disabled={
                  extractionQuery.isFetching
                  || generateMutation.isPending
                  || deleteMutation.isPending
                }
                onClick={() => {
                  void extractionQuery.refetch();
                }}
              >
                {extractionQuery.isFetching
                  ? "Refreshing…"
                  : "Refresh stored"}
              </button>

              <button
                className="button button--primary"
                type="button"
                disabled={
                  generateMutation.isPending
                  || deleteMutation.isPending
                }
                onClick={() =>
                  setRegenerateDialogOpen(
                    true,
                  )
                }
              >
                Regenerate
              </button>

              <button
                className="button button--danger"
                type="button"
                disabled={
                  generateMutation.isPending
                  || deleteMutation.isPending
                }
                onClick={() =>
                  setDeleteDialogOpen(
                    true,
                  )
                }
              >
                Delete extraction
              </button>
            </>
          )}
        </div>
      </section>

      {extractionQuery.isLoading && (
        <div
          className="document-state"
          role="status"
        >
          Checking for a stored extraction…
        </div>
      )}

      {generateMutation.isPending && (
        <section
          className="extraction-progress"
          role="status"
          aria-live="polite"
        >
          <div className="query-spinner" />

          <div>
            <strong>
              {elapsedMessage(
                elapsedSeconds,
              )}
            </strong>

            <p>
              Elapsed time:{" "}
              {elapsedSeconds}
              {" seconds"}
            </p>
          </div>
        </section>
      )}

      {generationMessage && (
        <StatusBanner tone="success">
          {generationMessage}
        </StatusBanner>
      )}

      {generateError && (
        <StatusBanner tone="error">
          {generateError}
        </StatusBanner>
      )}

      {deleteError && (
        <StatusBanner tone="error">
          {deleteError}
        </StatusBanner>
      )}

      {extractionLoadError && (
        <StatusBanner tone="error">
          {extractionLoadError}
        </StatusBanner>
      )}

      {selectedDocumentId
        && !extractionQuery.isLoading
        && !persistedExtraction
        && !generateMutation.isPending
        && !generateError && (
          <section className="answer-empty">
            <h3>
              No stored extraction
            </h3>

            <p>
              Generate an extraction to create
              structured patient, provider,
              diagnosis, medication, laboratory,
              procedure, and follow-up fields.
            </p>
          </section>
        )}

      {!selectedDocumentId && (
        <section className="answer-empty">
          <h3>
            Select one document
          </h3>

          <p>
            Structured extraction operates on one
            document at a time and stores one current
            extraction per document.
          </p>
        </section>
      )}

      {persistedExtraction
        && extraction && (
          <section className="extraction-result">
            <header className="extraction-result__header">
              <div>
                <p className="eyebrow">
                  Persisted extraction
                </p>

                <h3>
                  {humanize(
                    extraction.document_type,
                  )}
                </h3>
              </div>

              <div className="extraction-statuses">
                <span className="route-badge">
                  {humanize(
                    extraction.status,
                  )}
                </span>

                <span className="route-badge">
                  {humanize(
                    persistedExtraction
                      .extraction_method,
                  )}
                </span>
              </div>
            </header>

            <dl className="extraction-overview">
              <div>
                <dt>Confidence</dt>
                <dd>
                  {confidencePercent(
                    extraction
                      .extraction_confidence,
                  )}
                </dd>
              </div>

              <div>
                <dt>Model</dt>
                <dd>
                  {
                    persistedExtraction
                      .model_name
                  }
                </dd>
              </div>

              <div>
                <dt>Generated</dt>
                <dd>
                  {formatDateTime(
                    extraction.generated_at,
                  )}
                </dd>
              </div>

              <div>
                <dt>Stored</dt>
                <dd>
                  {formatDateTime(
                    persistedExtraction
                      .created_at,
                  )}
                </dd>
              </div>

              <div>
                <dt>Last updated</dt>
                <dd>
                  {formatDateTime(
                    persistedExtraction
                      .updated_at,
                  )}
                </dd>
              </div>

              <div>
                <dt>Extraction ID</dt>
                <dd title={
                  persistedExtraction
                    .extraction_id
                }>
                  {
                    persistedExtraction
                      .extraction_id
                  }
                </dd>
              </div>
            </dl>

            {extraction.warnings.length > 0 && (
              <section className="extraction-warning-panel">
                <div>
                  <p className="eyebrow">
                    Validation warnings
                  </p>

                  <h4>
                    Partial or limited extraction
                  </h4>
                </div>

                <ul>
                  {extraction.warnings.map(
                    (warning) => (
                      <li key={warning.code}>
                        <strong>
                          {humanize(
                            warning.code,
                          )}
                        </strong>
                        {": "}
                        {warning.message}
                      </li>
                    ),
                  )}
                </ul>
              </section>
            )}

            <section className="extraction-section">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">
                    Identity and dates
                  </p>

                  <h3>
                    Patient information
                  </h3>
                </div>

                <span>
                  {patientFacts.length}
                  {" fact"}
                  {patientFacts.length === 1
                    ? ""
                    : "s"}
                </span>
              </div>

              {patientFacts.length === 0 ? (
                <div className="extraction-empty">
                  No supported patient or document
                  date facts were extracted.
                </div>
              ) : (
                <div className="extraction-fact-grid">
                  {patientFacts.map(
                    (fact) => (
                      <ExtractionFactCard
                        key={fact.title}
                        title={fact.title}
                        details={
                          fact.date
                            ? sourcedDateDetails(
                              fact.value,
                            )
                            : sourcedTextDetails(
                              fact.value,
                            )
                        }
                        confidence={
                          fact.value.confidence
                        }
                        extractionMethod={
                          fact.value
                            .extraction_method
                        }
                        sources={
                          fact.value.sources
                        }
                      />
                    ),
                  )}
                </div>
              )}
            </section>

            <section className="extraction-section">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">
                    Care team
                  </p>

                  <h3>Providers</h3>
                </div>

                <span>
                  {extraction.providers.length}
                </span>
              </div>

              {extraction.providers.length === 0 ? (
                <div className="extraction-empty">
                  No supported providers were
                  extracted.
                </div>
              ) : (
                <div className="extraction-fact-grid">
                  {extraction.providers.map(
                    (provider, index) => (
                      <ExtractionFactCard
                        key={`${provider.name}-${index}`}
                        title={provider.name}
                        details={[
                          {
                            label: "Role",
                            value: provider.role,
                          },
                          {
                            label: "Organization",
                            value:
                              provider.organization,
                          },
                        ]}
                        confidence={
                          provider.confidence
                        }
                        extractionMethod={
                          provider
                            .extraction_method
                        }
                        sources={
                          provider.sources
                        }
                      />
                    ),
                  )}
                </div>
              )}
            </section>

            <section className="extraction-section">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">
                    Clinical findings
                  </p>

                  <h3>Diagnoses</h3>
                </div>

                <span>
                  {extraction.diagnoses.length}
                </span>
              </div>

              {extraction.diagnoses.length === 0 ? (
                <div className="extraction-empty">
                  No supported diagnoses were
                  extracted.
                </div>
              ) : (
                <div className="extraction-fact-grid">
                  {extraction.diagnoses.map(
                    (diagnosis, index) => (
                      <ExtractionFactCard
                        key={`${diagnosis.name}-${index}`}
                        title={diagnosis.name}
                        status={diagnosis.status}
                        details={[
                          {
                            label: "Code",
                            value: diagnosis.code,
                          },
                          {
                            label: "Code system",
                            value:
                              diagnosis.code_system,
                          },
                        ]}
                        confidence={
                          diagnosis.confidence
                        }
                        extractionMethod={
                          diagnosis
                            .extraction_method
                        }
                        sources={
                          diagnosis.sources
                        }
                      />
                    ),
                  )}
                </div>
              )}
            </section>

            <section className="extraction-section">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">
                    Treatment
                  </p>

                  <h3>Medications</h3>
                </div>

                <span>
                  {extraction.medications.length}
                </span>
              </div>

              {extraction.medications.length === 0 ? (
                <div className="extraction-empty">
                  No supported medications were
                  extracted.
                </div>
              ) : (
                <div className="extraction-fact-grid">
                  {extraction.medications.map(
                    (medication, index) => (
                      <ExtractionFactCard
                        key={`${medication.name}-${index}`}
                        title={medication.name}
                        status={medication.status}
                        details={[
                          {
                            label: "Dose",
                            value: medication.dose,
                          },
                          {
                            label: "Route",
                            value: medication.route,
                          },
                          {
                            label: "Frequency",
                            value:
                              medication.frequency,
                          },
                          {
                            label: "Duration",
                            value:
                              medication.duration,
                          },
                          {
                            label: "Instructions",
                            value:
                              medication.instructions,
                          },
                        ]}
                        confidence={
                          medication.confidence
                        }
                        extractionMethod={
                          medication
                            .extraction_method
                        }
                        sources={
                          medication.sources
                        }
                      />
                    ),
                  )}
                </div>
              )}
            </section>

            <section className="extraction-section">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">
                    Measurements
                  </p>

                  <h3>Laboratory results</h3>
                </div>

                <span>
                  {extraction.lab_results.length}
                </span>
              </div>

              {extraction.lab_results.length === 0 ? (
                <div className="extraction-empty">
                  No supported laboratory results
                  were extracted.
                </div>
              ) : (
                <div className="extraction-fact-grid">
                  {extraction.lab_results.map(
                    (lab, index) => (
                      <ExtractionFactCard
                        key={`${lab.test_name}-${index}`}
                        title={lab.test_name}
                        status={lab.flag}
                        details={[
                          {
                            label: "Result",
                            value: [
                              lab.raw_value,
                              lab.unit,
                            ]
                              .filter(Boolean)
                              .join(" "),
                          },
                          {
                            label: "Numeric value",
                            value:
                              lab.numeric_value,
                          },
                          {
                            label: "Reference range",
                            value:
                              lab.reference_range,
                          },
                          {
                            label: "Collected",
                            value:
                              lab.collected_at
                                ?.raw_value
                              ?? null,
                          },
                        ]}
                        confidence={lab.confidence}
                        extractionMethod={
                          lab.extraction_method
                        }
                        sources={mergeSources(
                          lab.sources,
                          lab.collected_at
                            ?.sources,
                        )}
                      />
                    ),
                  )}
                </div>
              )}
            </section>

            <section className="extraction-section">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">
                    Clinical actions
                  </p>

                  <h3>Procedures</h3>
                </div>

                <span>
                  {extraction.procedures.length}
                </span>
              </div>

              {extraction.procedures.length === 0 ? (
                <div className="extraction-empty">
                  No supported procedures were
                  extracted.
                </div>
              ) : (
                <div className="extraction-fact-grid">
                  {extraction.procedures.map(
                    (procedure, index) => (
                      <ExtractionFactCard
                        key={`${procedure.name}-${index}`}
                        title={procedure.name}
                        details={[
                          {
                            label: "Date",
                            value:
                              procedure
                                .procedure_date
                                ?.raw_value
                              ?? null,
                          },
                          {
                            label: "Result",
                            value:
                              procedure.result,
                          },
                        ]}
                        confidence={
                          procedure.confidence
                        }
                        extractionMethod={
                          procedure
                            .extraction_method
                        }
                        sources={mergeSources(
                          procedure.sources,
                          procedure
                            .procedure_date
                            ?.sources,
                        )}
                      />
                    ),
                  )}
                </div>
              )}
            </section>

            <section className="extraction-section">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">
                    Next steps
                  </p>

                  <h3>
                    Follow-up instructions
                  </h3>
                </div>

                <span>
                  {
                    extraction
                      .follow_up_instructions
                      .length
                  }
                </span>
              </div>

              {extraction
                .follow_up_instructions
                .length === 0 ? (
                <div className="extraction-empty">
                  No supported follow-up
                  instructions were extracted.
                </div>
              ) : (
                <div className="extraction-fact-grid">
                  {extraction
                    .follow_up_instructions
                    .map(
                      (instruction, index) => (
                        <ExtractionFactCard
                          key={`${instruction.instruction}-${index}`}
                          title={
                            instruction
                              .instruction
                          }
                          details={[
                            {
                              label: "Timeframe",
                              value:
                                instruction
                                  .timeframe,
                            },
                            {
                              label: "Specialty",
                              value:
                                instruction
                                  .specialty,
                            },
                          ]}
                          confidence={
                            instruction
                              .confidence
                          }
                          extractionMethod={
                            instruction
                              .extraction_method
                          }
                          sources={
                            instruction.sources
                          }
                        />
                      ),
                    )}
                </div>
              )}
            </section>
          </section>
        )}

      <section className="safety-panel">
        <div>
          <p className="eyebrow">
            Extraction boundary
          </p>

          <h3>
            Evidence-backed, not clinical advice
          </h3>
        </div>

        <p>
          Extracted fields summarize documented text.
          They do not diagnose, interpret undocumented
          meaning, or replace review by a licensed
          healthcare professional.
        </p>
      </section>

      <ConfirmDialog
        isOpen={regenerateDialogOpen}
        title="Regenerate this extraction?"
        description={
          "MIRA will run the extraction pipeline "
          + "again and replace the currently stored "
          + "structured result. The original "
          + "document will not be changed."
        }
        confirmLabel="Regenerate and replace"
        isConfirming={
          generateMutation.isPending
        }
        onCancel={() =>
          setRegenerateDialogOpen(
            false,
          )
        }
        onConfirm={() =>
          generate(true)
        }
      />

      <ConfirmDialog
        isOpen={deleteDialogOpen}
        title="Delete this extraction?"
        description={
          "The stored structured extraction will "
          + "be permanently deleted. The uploaded "
          + "document, chunks, and embeddings will "
          + "remain available."
        }
        confirmLabel="Delete extraction"
        isConfirming={
          deleteMutation.isPending
        }
        onCancel={() =>
          setDeleteDialogOpen(false)
        }
        onConfirm={() => {
          if (selectedDocumentId) {
            deleteMutation.mutate(
              selectedDocumentId,
            );
          }
        }}
      />
    </section>
  );
}