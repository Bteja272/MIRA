describe(
  "MIRA medical intelligence",
  () => {
    const documentOne = {
      document_id: "doc-1",
      filename:
        "synthetic-fracture.txt",
      document_type:
        "discharge_summary",
      file_size_bytes: 500,
      chunk_count: 2,
      uploaded_at:
        "2026-08-20T12:00:00Z",
    };

    const documentTwo = {
      document_id: "doc-2",
      filename:
        "synthetic-followup.txt",
      document_type:
        "visit_note",
      file_size_bytes: 400,
      chunk_count: 2,
      uploaded_at:
        "2026-08-21T12:00:00Z",
    };

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

    const intelligence = {
      intelligence_id:
        "intelligence-1",
      document_id: "doc-1",
      source_extraction_id:
        "extract-1",
      source_extraction_updated_at:
        "2026-08-20T12:00:00Z",
      schema_version: "1.0",
      status: "completed",
      created_at:
        "2026-08-20T12:00:00Z",
      updated_at:
        "2026-08-20T12:00:00Z",
      intelligence: {
        schema_version: "1.0",
        intelligence_id:
          "intelligence-1",
        document_id: "doc-1",
        source_extraction_id:
          "extract-1",
        source_extraction_updated_at:
          "2026-08-20T12:00:00Z",
        status: "completed",
        normalized_entities: [
          {
            entity_type:
              "diagnosis",
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
              "exact",
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
                "A fracture means that "
                + "a bone has been cracked "
                + "or broken."
              ),
            general_information: [
              (
                "Fracture care varies "
                + "according to the bone "
                + "involved."
              ),
            ],
            supportive_care: [
              (
                "Protect the injured area "
                + "and follow documented "
                + "instructions."
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
                "Seek urgent medical "
                + "evaluation for new "
                + "circulation or sensation "
                + "changes."
              ),
            questions_for_clinician: [
              (
                "What activity restrictions "
                + "apply to this injury?"
              ),
            ],
            guidance_level:
              "supportive",
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
        warnings: [],
        generated_at:
          "2026-08-20T12:00:00Z",
      },
    };

    beforeEach(() => {
      cy.intercept(
        "GET",
        "**/auth/me",
        {
          statusCode: 200,
          body: {
            user_id:
              "synthetic-user",
            email:
              "synthetic@example.com",
            is_active: true,
            created_at:
              "2026-08-20T10:00:00Z",
          },
        },
      );

      cy.intercept(
        "GET",
        "**/documents",
        {
          statusCode: 200,
          body: {
            documents: [
              documentOne,
              documentTwo,
            ],
            count: 2,
          },
        },
      );

      cy.intercept(
        "GET",
        "**/documents/doc-1/intelligence",
        {
          statusCode: 200,
          body: intelligence,
        },
      ).as(
        "getIntelligence",
      );

      cy.intercept(
        "POST",
        "**/documents/doc-1/intelligence",
        {
          statusCode: 200,
          body: {
            cached: false,
            replaced: true,
            extraction_generated:
              false,
            message:
              (
                "Medical intelligence "
                + "was regenerated from "
                + "the current structured "
                + "extraction."
              ),
            result:
              intelligence,
          },
        },
      ).as(
        "generateIntelligence",
      );

      cy.intercept(
        "DELETE",
        "**/documents/doc-1/intelligence",
        {
          statusCode: 200,
          body: {
            document_id:
              "doc-1",
            deleted: true,
            message:
              (
                "Stored medical "
                + "intelligence was deleted."
              ),
          },
        },
      ).as(
        "deleteIntelligence",
      );

      cy.intercept(
        "POST",
        "**/intelligence/timeline",
        {
          statusCode: 200,
          body: {
            document_ids: [
              "doc-1",
              "doc-2",
            ],
            events: [
              {
                event_id:
                  "combined-event-1",
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
                "Timeline entries "
                + "represent documented "
                + "events only."
              ),
            ],
            generated_at:
              "2026-08-22T12:00:00Z",
          },
        },
      ).as(
        "buildTimeline",
      );

      cy.intercept(
        "POST",
        "**/intelligence/compare",
        {
          statusCode: 200,
          body: {
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
                    "This item was found "
                    + "in the earlier selected "
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
                after_summary: null,
                sources: [
                  source,
                ],
              },
            ],
            notices: [
              (
                "Missing later findings "
                + "are not treated as "
                + "resolved."
              ),
            ],
            generated_at:
              "2026-08-22T12:00:00Z",
          },
        },
      ).as(
        "compareDocuments",
      );
    });

    it(
      "shows bounded guidance and longitudinal changes",
      () => {
        cy.visit(
          "/intelligence",
        );

        cy.findByLabelText(
          "Select a document",
        ).select(
          "doc-1",
        );

        cy.wait(
          "@getIntelligence",
        );

        cy.contains(
          "Distal radius fracture",
        ).should(
          "be.visible",
        );

        cy.contains(
          (
            "A fracture means that "
            + "a bone has been cracked "
            + "or broken."
          ),
        ).should(
          "be.visible",
        );

        cy.contains(
          (
            "New or worsening numbness "
            + "or loss of sensation."
          ),
        ).should(
          "be.visible",
        );

        cy.contains(
          (
            "Education, not diagnosis "
            + "or treatment"
          ),
        ).should(
          "be.visible",
        );

        cy.findByLabelText(
            "synthetic-fracture.txt",
            ).check();

            cy.findByLabelText(
            "synthetic-followup.txt",
            ).check();

        cy.findByRole(
          "button",
          {
            name:
              "Build longitudinal view",
          },
        ).click();

        cy.wait(
          "@buildTimeline",
        );

        cy.wait(
          "@compareDocuments",
        );

        cy.contains(
          "Documented changes",
        ).should(
          "be.visible",
        );

        cy.contains(
          (
            "does not establish that "
            + "the condition resolved"
          ),
        ).should(
          "be.visible",
        );

        cy.contains(
          /condition improved/i,
        ).should(
          "not.exist",
        );

        cy.contains(
          /condition worsened/i,
        ).should(
          "not.exist",
        );
      },
    );

    it(
      "regenerates and deletes stored intelligence",
      () => {
        cy.visit(
          "/intelligence",
        );

        cy.findByLabelText(
          "Select a document",
        ).select(
          "doc-1",
        );

        cy.wait(
          "@getIntelligence",
        );

        cy.findByRole(
          "button",
          {
            name:
              "Regenerate",
          },
        ).click();

        cy.wait(
          "@generateIntelligence",
        );

        cy.contains(
          (
            "Medical intelligence "
            + "was regenerated"
          ),
        ).should(
          "be.visible",
        );

        cy.findByRole(
          "button",
          {
            name:
              "Delete intelligence",
          },
        ).click();

        cy.wait(
          "@deleteIntelligence",
        );

        cy.contains(
          (
            "Stored medical "
            + "intelligence was deleted."
          ),
        ).should(
          "be.visible",
        );
      },
    );
  },
);