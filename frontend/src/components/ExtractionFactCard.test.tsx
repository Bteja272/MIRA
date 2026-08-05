import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
} from "vitest";

import {
  ExtractionFactCard,
} from "./ExtractionFactCard";

describe(
  "ExtractionFactCard",
  () => {
    it(
      "renders confidence, extraction method, details, and evidence",
      async () => {
        render(
          <ExtractionFactCard
            title="Lisinopril"
            status="current"
            confidence={0.91}
            extractionMethod="hybrid"
            details={[
              {
                label: "Dose",
                value: "10 mg",
              },
              {
                label: "Frequency",
                value: "Once daily",
              },
            ]}
            sources={[
              {
                document_id: "doc-1",
                chunk_id: "chunk-1",
                source_filename:
                  "synthetic.txt",
                page_number: null,
                chunk_index: 0,
                quoted_text:
                  "Lisinopril 10 mg by mouth once daily.",
              },
            ]}
          />,
        );

        expect(
          screen.getByText(
            "Lisinopril",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "91%",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Hybrid",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "10 mg",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /View 1 evidence source/i,
          ),
        ).toBeInTheDocument();
      },
    );
  },
);