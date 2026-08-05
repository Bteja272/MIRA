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
  SourceCard,
} from "./SourceCard";

describe(
  "SourceCard",
  () => {
    it(
      "renders a web source title and safe link",
      () => {
        render(
          <SourceCard
            index={0}
            source={{
              source_number: 1,
              title:
                "Blood Pressure Guide",
              url:
                "https://example.com/blood-pressure",
              content:
                "Systolic pressure is measured when the heart contracts.",
            }}
          />,
        );

        expect(
          screen.getByText(
            "Web Source 1",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Blood Pressure Guide",
            },
          ),
        ).toHaveAttribute(
          "href",
          "https://example.com/blood-pressure",
        );
      },
    );

    it(
      "renders document evidence without an external link",
      () => {
        render(
          <SourceCard
            index={0}
            source={{
              source_filename:
                "synthetic.txt",
              document_id: "doc-1",
              chunk_id: "chunk-1",
              chunk_index: 0,
              text:
                "Lisinopril 10 mg once daily.",
            }}
          />,
        );

        expect(
          screen.getByText(
            "synthetic.txt",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByRole(
            "link",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByText(
            "Lisinopril 10 mg once daily.",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);