import {
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
  getDocuments,
} from "../api/documents";
import {
  buildMedicalTimeline,
  compareMedicalDocuments,
  deleteIntelligence,
  generateIntelligence,
  getIntelligenceOrNull,
} from "../api/intelligence";
import {
  MedicalIntelligencePage,
} from "./MedicalIntelligencePage";
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
  "../api/intelligence",
  () => ({
    buildMedicalTimeline: vi.fn(),
    compareMedicalDocuments: vi.fn(),
    deleteIntelligence: vi.fn(),
    generateIntelligence: vi.fn(),
    getIntelligenceOrNull: vi.fn(),
  }),
);


const mockedGetDocuments =
  vi.mocked(getDocuments);

const mockedGetIntelligenceOrNull =
  vi.mocked(
    getIntelligenceOrNull,
  );

const mockedGenerateIntelligence =
  vi.mocked(
    generateIntelligence,
  );

const mockedDeleteIntelligence =
  vi.mocked(
    deleteIntelligence,
  );

const mockedBuildMedicalTimeline =
  vi.mocked(
    buildMedicalTimeline,
  );

const mockedCompareMedicalDocuments =
  vi.mocked(
    compareMedicalDocuments,
  );


const source = {
  document_id: "doc-1",
  chunk_id: "chunk-1",
  source_filename:
    "synthetic-fracture.txt",
  page_number: 1,
  chunk_index: 0,
  quoted_text:
    "Closed distal radius fracture.",
};


const persistedIntelligence = {
  intelligence_id:
    "intelligence-1",
  document_id: "doc-1",
  source_extraction_id:
    "extract-1",
  source_extraction_updated_at:
    "2026-08-20T12:00:00Z",
  schema_version: "1.0",
  status: "completed" as const,
  created_at:
    "2026-08-20T12:00:00Z",
  updated_at:
    "2026-08-20T12:00:00Z",
  intelligence: {
    schema_version:
      "1.0" as const,
    intelligence_id:
      "intelligence-1",
    document_id: "doc-1",
    source_extraction_id:
      "extract-1",
    source_extraction_updated_at:
      "2026-08-20T12:00:00Z",
    status: "completed" as const,
    normalized_entities: [
      {
        entity_type:
          "diagnosis" as const,
        raw_name:
          "Distal radius fracture",
        normalized_name:
          "Distal radius fracture",
        canonical_key:
          (
            "diagnosis:"
            + "distal radius fracture"
          ),
        code: null,
        code_system: null,
        status: "active",
        confidence: 0.98,
        normalization_method:
          "exact" as const,
        details: {},
        sources: [
          source,
        ],
      },
    ],
    guidance_cards: [
      {
        topic:
          "Distal radius fracture",
        documented_fact: {
          category:
            "diagnosis",
          label:
            "Documented finding",
          value:
            (
              "Distal radius fracture "
              + "(documented status: active)"
            ),
          sources: [
            source,
          ],
        },
        plain_language_explanation:
          (
            "A fracture means that a bone "
            + "has been cracked or broken."
          ),
        general_information: [
          (
            "Fracture care varies according "
            + "to the bone involved."
          ),
        ],
        supportive_care: [
          (
            "Protect the injured area and "
            + "follow documented instructions."
          ),
        ],
        red_flags: [
          (
            "New or worsening numbness "
            + "or loss of sensation."
          ),
        ],
        when_to_seek_care:
          (
            "Seek urgent medical evaluation "
            + "for new circulation or "
            + "sensation changes."
          ),
        questions_for_clinician: [
          (
            "What activity restrictions "
            + "apply to this injury?"
          ),
        ],
        guidance_level:
          "supportive" as const,
        safety_flags: [
          "documented_condition_only",
          "no_medication_changes",
          "no_medication_dosing",
        ],
        sources: [
          source,
        ],
      },
    ],
    timeline_events: [
      {
        event_id: "event-1",
        document_id: "doc-1",
        event_type:
          "diagnosis" as const,
        title:
          "Distal radius fracture",
        detail:
          (
            "Documented diagnosis "
            + "status: active."
          ),
        event_date:
          "2026-08-20",
        sources: [
          source,
        ],
      },
    ],
    warnings: [],
    generated_at:
      "2026-08-20T12:00:00Z",
  },
};


describe(
  "MedicalIntelligencePage",
  () => {
    beforeEach(() => {
      mockedGetDocuments.mockResolvedValue({
        documents: [
          {
            document_id: "doc-1",
            filename:
              "synthetic-fracture.txt",
            document_type:
              "discharge_summary",
            file_size_bytes: 500,
            chunk_count: 2,
            uploaded_at:
              "2026-08-20T12:00:00Z",
          },
          {
            document_id: "doc-2",
            filename:
              "synthetic-followup.txt",
            document_type:
              "visit_note",
            file_size_bytes: 400,
            chunk_count: 2,
            uploaded_at:
              "2026-08-21T12:00:00Z",
          },
        ],
        count: 2,
      });

      mockedGetIntelligenceOrNull
        .mockResolvedValue(
          persistedIntelligence,
        );

      mockedGenerateIntelligence
        .mockResolvedValue({
          cached: false,
          replaced: false,
          extraction_generated:
            false,
          message:
            (
              "Medical intelligence "
              + "was generated and stored."
            ),
          result:
            persistedIntelligence,
        });

      mockedDeleteIntelligence
        .mockResolvedValue({
          document_id: "doc-1",
          deleted: true,
          message:
            (
              "Stored medical intelligence "
              + "was deleted."
            ),
        });

      mockedBuildMedicalTimeline
        .mockResolvedValue({
          document_ids: [
            "doc-1",
            "doc-2",
          ],
          events: [
            {
              event_id:
                "event-combined-1",
              document_id:
                "doc-1",
              event_type:
                "diagnosis",
              title:
                "Distal radius fracture",
              detail:
                (
                  "Documented diagnosis "
                  + "status: active."
                ),
              event_date:
                "2026-08-20",
              sources: [
                source,
              ],
            },
          ],
          notices: [
            (
              "Timeline entries represent "
              + "documented events only."
            ),
          ],
          generated_at:
            "2026-08-22T12:00:00Z",
        });

      mockedCompareMedicalDocuments
        .mockResolvedValue({
          document_ids: [
            "doc-1",
            "doc-2",
          ],
          changes: [
            {
              entity_type:
                "diagnosis",
              canonical_key:
                (
                  "diagnosis:"
                  + "distal radius fracture"
                ),
              normalized_name:
                "Distal radius fracture",
              change_type:
                "not_mentioned_later",
              from_document_id:
                "doc-1",
              to_document_id:
                "doc-2",
              description:
                (
                  "This item was found in "
                  + "the earlier selected "
                  + "record but was not found "
                  + "in the later selected "
                  + "record. This does not "
                  + "establish that the "
                  + "condition resolved."
                ),
              before_summary:
                (
                  "Distal radius fracture; "
                  + "status=active"
                ),
              after_summary:
                null,
              sources: [
                source,
              ],
            },
          ],
          notices: [
            (
              "A finding absent from a later "
              + "record is not treated as "
              + "resolved."
            ),
          ],
          generated_at:
            "2026-08-22T12:00:00Z",
        });
    });


    it(
      "displays normalized entities and bounded guidance",
      async () => {
        const user =
          userEvent.setup();

        renderWithQueryClient(
          <MedicalIntelligencePage />,
        );

        const documentSelect =
        await screen.findByLabelText(
            "Select a document",
        );

        await waitFor(() => {
        expect(
            screen.getByRole(
            "option",
            {
                name:
                /synthetic-fracture\.txt/i,
            },
            ),
        ).toBeInTheDocument();
        });

        await user.selectOptions(
        documentSelect,
        "doc-1",
        );

        const fractureMentions =
        await screen.findAllByText(
            "Distal radius fracture",
        );

        expect(
        fractureMentions.length,
        ).toBeGreaterThanOrEqual(1);

        expect(
          screen.getByText(
            (
              "A fracture means that a bone "
              + "has been cracked or broken."
            ),
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            (
              "New or worsening numbness "
              + "or loss of sensation."
            ),
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            (
              "What activity restrictions "
              + "apply to this injury?"
            ),
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            (
              "Education, not diagnosis "
              + "or treatment"
            ),
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "builds longitudinal timeline and safe comparison wording",
      async () => {
        const user =
          userEvent.setup();

        renderWithQueryClient(
          <MedicalIntelligencePage />,
        );

        const first =
          await screen.findByLabelText(
            "synthetic-fracture.txt",
          );

        const second =
          screen.getByLabelText(
            "synthetic-followup.txt",
          );

        await user.click(first);
        await user.click(second);

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Build longitudinal view",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockedBuildMedicalTimeline,
          ).toHaveBeenCalledWith([
            "doc-1",
            "doc-2",
          ]);

          expect(
            mockedCompareMedicalDocuments,
          ).toHaveBeenCalledWith([
            "doc-1",
            "doc-2",
          ]);
        });

        expect(
          await screen.findByText(
            "Documented changes",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /does not establish that the condition resolved/i,
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            /condition improved/i,
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            /condition worsened/i,
          ),
        ).not.toBeInTheDocument();
      },
    );


    it(
      "deletes only stored intelligence",
      async () => {
        const user =
          userEvent.setup();

        renderWithQueryClient(
          <MedicalIntelligencePage />,
        );

        const documentSelect =
        await screen.findByLabelText(
            "Select a document",
        );

        await waitFor(() => {
        expect(
            screen.getByRole(
            "option",
            {
                name:
                /synthetic-fracture\.txt/i,
            },
            ),
        ).toBeInTheDocument();
        });

        await user.selectOptions(
        documentSelect,
        "doc-1",
        );

        await screen.findAllByText(
          "Distal radius fracture",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Delete intelligence",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockedDeleteIntelligence,
          ).toHaveBeenCalledWith(
            "doc-1",
          );
        });

        expect(
          await screen.findByText(
            (
              "Stored medical intelligence "
              + "was deleted."
            ),
          ),
        ).toBeInTheDocument();
      },
    );
  },
);