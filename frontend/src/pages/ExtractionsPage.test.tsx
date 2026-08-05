import {
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  getDocuments,
} from "../api/documents";
import {
  deleteExtraction,
  generateExtraction,
  getExtractionOrNull,
} from "../api/extractions";
import {
  ExtractionsPage,
} from "./ExtractionsPage";
import {
  renderWithQueryClient,
} from "../test/renderWithQueryClient";
import type {
  PersistedMedicalExtraction,
} from "../types/extractions";

vi.mock(
  "../api/documents",
  () => ({
    getDocuments: vi.fn(),
  }),
);

vi.mock(
  "../api/extractions",
  () => ({
    getExtractionOrNull:
      vi.fn(),
    generateExtraction:
      vi.fn(),
    deleteExtraction:
      vi.fn(),
  }),
);

const mockedGetDocuments =
  vi.mocked(getDocuments);

const mockedGetExtractionOrNull =
  vi.mocked(getExtractionOrNull);

const mockedGenerateExtraction =
  vi.mocked(generateExtraction);

const mockedDeleteExtraction =
  vi.mocked(deleteExtraction);

const persistedExtraction:
  PersistedMedicalExtraction = {
    extraction_id: "extract-1",
    document_id: "doc-1",
    schema_version: "1.0",
    status: "completed",
    extraction_method: "hybrid",
    model_name: "llama3.2",
    created_at:
      "2026-08-05T18:00:00Z",
    updated_at:
      "2026-08-05T18:00:00Z",
    extraction: {
      schema_version: "1.0",
      extraction_id: "extract-1",
      document_id: "doc-1",
      document_type:
        "discharge_summary",
      status: "completed",
      patient: {
        name: {
          value:
            "Synthetic Patient",
          confidence: 0.98,
          extraction_method:
            "deterministic",
          sources: [],
        },
        date_of_birth: null,
        medical_record_number:
          null,
      },
      document_date: null,
      providers: [],
      diagnoses: [
        {
          name: "Hypertension",
          code: null,
          code_system: null,
          status: "active",
          confidence: 0.9,
          extraction_method:
            "hybrid",
          sources: [],
        },
      ],
      medications: [
        {
          name: "Lisinopril",
          dose: "10 mg",
          route: "By mouth",
          frequency: "Once daily",
          duration: null,
          instructions: null,
          status: "current",
          confidence: 0.91,
          extraction_method:
            "hybrid",
          sources: [],
        },
      ],
      lab_results: [],
      procedures: [],
      follow_up_instructions: [],
      warnings: [],
      extraction_confidence: 0.89,
      generated_at:
        "2026-08-05T18:00:00Z",
    },
  };

describe(
  "ExtractionsPage",
  () => {
    beforeEach(() => {
      mockedGetDocuments.mockResolvedValue({
        documents: [
          {
            document_id: "doc-1",
            filename: "synthetic.txt",
            document_type:
              "discharge_summary",
            file_size_bytes: 200,
            chunk_count: 2,
            uploaded_at:
              "2026-08-05T18:00:00Z",
          },
        ],
        count: 1,
      });

      mockedGetExtractionOrNull.mockResolvedValue(
        persistedExtraction,
      );

      mockedGenerateExtraction.mockResolvedValue({
        cached: false,
        replaced: true,
        message:
          "Extraction completed.",
        result:
          persistedExtraction,
      });

      mockedDeleteExtraction.mockResolvedValue({
        document_id: "doc-1",
        deleted: true,
        message:
          "The stored structured extraction was deleted.",
      });
    });

    it(
      "loads and displays a persisted extraction",
      async () => {
        const user =
          userEvent.setup();

        renderWithQueryClient(
          <ExtractionsPage />,
        );

        await screen.findByRole(
          "option",
          {
            name:
              /synthetic\.txt/i,
          },
        );

        await user.selectOptions(
          screen.getByLabelText(
            "Select a document",
          ),
          "doc-1",
        );

        expect(
          await screen.findByText(
            "Synthetic Patient",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Lisinopril",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "89% confidence",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "deletes only the stored extraction",
      async () => {
        const user =
          userEvent.setup();

        renderWithQueryClient(
          <ExtractionsPage />,
        );

        await screen.findByRole(
          "option",
          {
            name:
              /synthetic\.txt/i,
          },
        );

        await user.selectOptions(
          screen.getByLabelText(
            "Select a document",
          ),
          "doc-1",
        );

        await screen.findByText(
          "Synthetic Patient",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Delete extraction",
            },
          ),
        );

        const deleteButtons =
          screen.getAllByRole(
            "button",
            {
              name:
                "Delete extraction",
            },
          );

        await user.click(
          deleteButtons[
            deleteButtons.length - 1
          ],
        );

        expect(
          mockedDeleteExtraction,
        ).toHaveBeenCalledWith(
          "doc-1",
        );

        expect(
          await screen.findByText(
            "The stored structured extraction was deleted.",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);