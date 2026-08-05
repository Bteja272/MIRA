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
  queryMira,
} from "../api/query";
import {
  AskMiraPage,
} from "./AskMiraPage";
import {
  renderWithQueryClient,
} from "../test/renderWithQueryClient";

vi.mock(
  "../api/documents",
  () => ({
    getDocuments: vi.fn(),
  }),
);

vi.mock(
  "../api/query",
  () => ({
    queryMira: vi.fn(),
  }),
);

const mockedGetDocuments =
  vi.mocked(getDocuments);

const mockedQueryMira =
  vi.mocked(queryMira);

describe(
  "AskMiraPage",
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
    });

    it(
      "submits a direct question without document IDs",
      async () => {
        const user =
          userEvent.setup();

        mockedQueryMira.mockResolvedValue({
          query:
            "What is systolic blood pressure?",
          answer:
            "Systolic pressure is measured when the heart contracts.",
          route: "direct",
          document_id: null,
          document_ids: [],
          selected_document_count: 0,
          sources: [],
        });

        renderWithQueryClient(
          <AskMiraPage />,
        );

        await screen.findByText(
          "synthetic.txt",
        );

        await user.type(
          screen.getByLabelText(
            "Your question",
          ),
          "What is systolic blood pressure?",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name: "Ask MIRA",
            },
          ),
        );

        expect(
          await screen.findByText(
            "Systolic pressure is measured when the heart contracts.",
          ),
        ).toBeInTheDocument();

        expect(
          mockedQueryMira,
        ).toHaveBeenCalledWith(
          {
            query:
              "What is systolic blood pressure?",
            document_ids: undefined,
          },
          expect.any(
            AbortSignal,
          ),
        );
      },
    );

    it(
      "submits a document-grounded question and renders its source",
      async () => {
        const user =
          userEvent.setup();

        mockedQueryMira.mockResolvedValue({
          query:
            "What medication is listed?",
          answer:
            "Lisinopril 10 mg once daily is listed.",
          route: "rag",
          document_id: "doc-1",
          document_ids: [
            "doc-1",
          ],
          selected_document_count: 1,
          sources: [
            {
              source_filename:
                "synthetic.txt",
              document_id: "doc-1",
              chunk_id: "chunk-1",
              chunk_index: 0,
              text:
                "Lisinopril 10 mg once daily.",
            },
          ],
        });

        renderWithQueryClient(
          <AskMiraPage />,
        );

        await user.click(
          await screen.findByRole(
            "checkbox",
            {
              name: /synthetic\.txt/i,
            },
          ),
        );

        await user.type(
          screen.getByLabelText(
            "Your question",
          ),
          "What medication is listed?",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name: "Ask MIRA",
            },
          ),
        );

        expect(
          await screen.findByText(
            "Lisinopril 10 mg once daily is listed.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "synthetic.txt",
          ).length,
        ).toBeGreaterThanOrEqual(1);

        expect(
          mockedQueryMira,
        ).toHaveBeenCalledWith(
          {
            query:
              "What medication is listed?",
            document_ids: [
              "doc-1",
            ],
          },
          expect.any(
            AbortSignal,
          ),
        );
      },
    );
  },
);