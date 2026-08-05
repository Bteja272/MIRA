import {
  fireEvent,
  screen,
  waitFor,
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
  deleteDocument,
  getDocuments,
  uploadDocument,
} from "../api/documents";
import {
  DocumentsPage,
} from "./DocumentsPage";
import {
  renderWithQueryClient,
} from "../test/renderWithQueryClient";

vi.mock(
  "../api/documents",
  () => ({
    getDocuments: vi.fn(),
    getDocument: vi.fn(),
    uploadDocument: vi.fn(),
    deleteDocument: vi.fn(),
  }),
);

const mockedGetDocuments =
  vi.mocked(getDocuments);

const mockedUploadDocument =
  vi.mocked(uploadDocument);

const mockedDeleteDocument =
  vi.mocked(deleteDocument);

const documentRecord = {
  document_id: "doc-1",
  filename: "synthetic.txt",
  document_type:
    "discharge_summary",
  file_size_bytes: 200,
  chunk_count: 2,
  uploaded_at:
    "2026-08-05T18:00:00Z",
};

describe(
  "DocumentsPage",
  () => {
    beforeEach(() => {
      mockedGetDocuments.mockResolvedValue({
        documents: [
          documentRecord,
        ],
        count: 1,
      });

      mockedUploadDocument.mockResolvedValue({
        duplicate: false,
        document_id: "doc-2",
        existing_document_id: null,
        filename:
          "new-synthetic.txt",
        document_type:
          "discharge_summary",
        file_size_bytes: 150,
        chunks_indexed: 1,
        message:
          "Document uploaded successfully.",
        development_notice:
          "Synthetic data only.",
      });

      mockedDeleteDocument.mockResolvedValue({
        document_id: "doc-1",
        filename: "synthetic.txt",
        deleted: true,
        file_deleted: true,
      });
    });

    it(
      "rejects an unsupported file type before upload",
      async () => {
        const {
          container,
        } = renderWithQueryClient(
          <DocumentsPage />,
        );

        await screen.findByText(
          "synthetic.txt",
        );

        const input =
          container.querySelector(
            'input[type="file"]',
          ) as HTMLInputElement | null;

        expect(input).not.toBeNull();

        const invalidFile =
          new File(
            [
              "invalid",
            ],
            "invalid.csv",
            {
              type: "text/csv",
            },
          );

        // fireEvent is intentional here. userEvent respects the
        // input's accept attribute and filters the invalid file
        // before React receives the change event.
        fireEvent.change(
          input as HTMLInputElement,
          {
            target: {
              files: [
                invalidFile,
              ],
            },
          },
        );

        expect(
          await screen.findByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Only PDF and TXT files are allowed.",
        );

        expect(
          mockedUploadDocument,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "shows the duplicate response without creating another card",
      async () => {
        const user =
          userEvent.setup();

        mockedUploadDocument.mockResolvedValueOnce({
          duplicate: true,
          document_id: null,
          existing_document_id:
            "doc-1",
          filename: "synthetic.txt",
          document_type:
            "discharge_summary",
          file_size_bytes: 200,
          chunks_indexed: null,
          message:
            "This file has already been uploaded to your account.",
          development_notice:
            "Synthetic data only.",
        });

        const {
          container,
        } = renderWithQueryClient(
          <DocumentsPage />,
        );

        await screen.findByText(
          "synthetic.txt",
        );

        const input =
          container.querySelector(
            'input[type="file"]',
          ) as HTMLInputElement;

        await user.upload(
          input,
          new File(
            [
              "synthetic content",
            ],
            "synthetic.txt",
            {
              type: "text/plain",
            },
          ),
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Upload document",
            },
          ),
        );

        const statusBanner =
          await screen.findByRole(
            "status",
          );

        expect(
          statusBanner,
        ).toHaveTextContent(
          "This file has already been uploaded to your account.",
        );

        expect(
          statusBanner,
        ).toHaveTextContent(
          "Existing document ID:",
        );

        expect(
          statusBanner,
        ).toHaveTextContent(
          "doc-1",
        );

        expect(
          screen.getAllByText(
            "synthetic.txt",
          ),
        ).toHaveLength(1);
      },
    );

    it(
      "permanently deletes a document after confirmation",
      async () => {
        const user =
          userEvent.setup();

        mockedGetDocuments
          .mockResolvedValueOnce({
            documents: [
              documentRecord,
            ],
            count: 1,
          })
          .mockResolvedValue({
            documents: [],
            count: 0,
          });

        renderWithQueryClient(
          <DocumentsPage />,
        );

        await screen.findByText(
          "synthetic.txt",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Delete synthetic.txt",
            },
          ),
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Delete permanently",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockedDeleteDocument,
          ).toHaveBeenCalledWith(
            "doc-1",
          );
        });

        expect(
          await screen.findByText(
            "No documents yet",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);