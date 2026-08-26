import type {
  SourceEvidence,
} from "./extractions";

export type IntelligenceStatus =
  | "completed"
  | "partial";

export type MedicalEntityType =
  | "diagnosis"
  | "medication"
  | "lab"
  | "procedure"
  | "provider";

export type NormalizationMethod =
  | "exact"
  | "alias"
  | "documented_code";

export type GuidanceLevel =
  | "education"
  | "supportive"
  | "urgent_warning";

export type TimelineEventType =
  | "diagnosis"
  | "medication"
  | "lab"
  | "procedure"
  | "follow_up";

export type ChangeType =
  | "appeared"
  | "not_mentioned_later"
  | "status_changed"
  | "value_changed";

export interface NormalizedMedicalEntity {
  entity_type: MedicalEntityType;
  raw_name: string;
  normalized_name: string;
  canonical_key: string;
  code: string | null;
  code_system: string | null;
  status: string | null;
  confidence: number;
  normalization_method:
    NormalizationMethod;
  details: Record<string, unknown>;
  sources: SourceEvidence[];
}

export interface DocumentedMedicalFact {
  category: string;
  label: string;
  value: string;
  sources: SourceEvidence[];
}

export interface MedicalGuidanceCard {
  topic: string;
  documented_fact:
    DocumentedMedicalFact;
  plain_language_explanation: string;
  general_information: string[];
  supportive_care: string[];
  red_flags: string[];
  when_to_seek_care: string | null;
  questions_for_clinician: string[];
  guidance_level: GuidanceLevel;
  safety_flags: string[];
  sources: SourceEvidence[];
}

export interface MedicalTimelineEvent {
  event_id: string;
  document_id: string;
  event_type: TimelineEventType;
  title: string;
  detail: string | null;
  event_date: string | null;
  sources: SourceEvidence[];
}

export interface MedicalRecordChange {
  entity_type: MedicalEntityType;
  canonical_key: string;
  normalized_name: string;
  change_type: ChangeType;
  from_document_id: string;
  to_document_id: string;
  description: string;
  before_summary: string | null;
  after_summary: string | null;
  sources: SourceEvidence[];
}

export interface MedicalDocumentIntelligence {
  schema_version: "1.0";
  intelligence_id: string | null;
  document_id: string;
  source_extraction_id: string;
  source_extraction_updated_at: string;
  status: IntelligenceStatus;
  normalized_entities:
    NormalizedMedicalEntity[];
  guidance_cards:
    MedicalGuidanceCard[];
  timeline_events:
    MedicalTimelineEvent[];
  warnings: string[];
  generated_at: string;
}

export interface PersistedMedicalIntelligence {
  intelligence_id: string;
  document_id: string;
  source_extraction_id: string;
  source_extraction_updated_at: string;
  schema_version: string;
  status: IntelligenceStatus;
  intelligence:
    MedicalDocumentIntelligence;
  created_at: string;
  updated_at: string;
}

export interface IntelligenceGenerateResponse {
  cached: boolean;
  replaced: boolean;
  extraction_generated: boolean;
  message: string;
  result: PersistedMedicalIntelligence;
}

export interface IntelligenceDeleteResponse {
  document_id: string;
  deleted: boolean;
  message: string;
}

export interface IntelligenceTimelineResponse {
  document_ids: string[];
  events: MedicalTimelineEvent[];
  notices: string[];
  generated_at: string;
}

export interface IntelligenceCompareResponse {
  document_ids: string[];
  changes: MedicalRecordChange[];
  notices: string[];
  generated_at: string;
}