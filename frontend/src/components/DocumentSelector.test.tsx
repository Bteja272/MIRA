import {
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  DocumentSelector,
} from "./DocumentSelector";
import type {
  DocumentSummary,
} from "../types/documents";

const documents: DocumentSummary[] = [
  {
    document_id: "doc-1",
    filename: "first.txt",
    document_type:
      "discharge_summary",
    file_size_bytes: 100,
    chunk_count: 2,
    uploaded_at:
      "2026-08-05T18:00:00Z",
  },
  {
    document_id: "doc-2",
    filename: "second.txt",
    document_type:
      "lab_report",
    file_size_bytes: 200,
    chunk_count: 1,
    uploaded_at:
      "2026-08-05T18:00:00Z",
  },
];

describe(
  "DocumentSelector",
  () => {
    it(
      "selects and deselects documents",
      async () => {
        const user =
          userEvent.setup();

        const onChange = vi.fn();

        const {
          rerender,
        } = render(
          <DocumentSelector
            documents={documents}
            selectedIds={[]}
            maximumSelected={2}
            onChange={onChange}
          />,
        );

        await user.click(
          screen.getByRole(
            "checkbox",
            {
              name: /first\.txt/i,
            },
          ),
        );

        expect(
          onChange,
        ).toHaveBeenCalledWith([
          "doc-1",
        ]);

        rerender(
          <DocumentSelector
            documents={documents}
            selectedIds={[
              "doc-1",
            ]}
            maximumSelected={2}
            onChange={onChange}
          />,
        );

        await user.click(
          screen.getByRole(
            "checkbox",
            {
              name: /first\.txt/i,
            },
          ),
        );

        expect(
          onChange,
        ).toHaveBeenLastCalledWith(
          [],
        );
      },
    );

    it(
      "disables unselected options after reaching the selection limit",
      () => {
        render(
          <DocumentSelector
            documents={documents}
            selectedIds={[
              "doc-1",
            ]}
            maximumSelected={1}
            onChange={vi.fn()}
          />,
        );

        expect(
          screen.getByRole(
            "checkbox",
            {
              name: /second\.txt/i,
            },
          ),
        ).toBeDisabled();
      },
    );
  },
);