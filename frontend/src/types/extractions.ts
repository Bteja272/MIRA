export type ExtractionStatus =
  | "completed"
  | "partial"
  | "failed";

export type ExtractionMethod =
  | "deterministic"
  | "llm"
  | "hybrid";

export type MedicalDocumentType =
  | "lab_report"
  | "discharge_summary"
  | "prescription"
  | "imaging_report"
  | "pathology_report"
  | "visit_note"
  | "vaccination_record"
  | "insurance_document"
  | "unknown";

export type LabResultFlag =
  | "high"
  | "low"
  | "normal"
  | "abnormal"
  | "critical"
  | "positive"
  | "negative"
  | "unknown";

export type MedicationStatus =
  | "current"
  | "historical"
  | "discontinued"
  | "as_needed"
  | "unknown";

export type DiagnosisStatus =
  | "active"
  | "resolved"
  | "historical"
  | "ruled_out"
  | "unknown";

export interface SourceEvidence {
  document_id: string;
  chunk_id: string;
  source_filename: string | null;
  page_number: number | null;
  chunk_index: number;
  quoted_text: string;
}

export interface SourcedTextValue {
  value: string;
  confidence: number;
  extraction_method: ExtractionMethod;
  sources: SourceEvidence[];
}

export interface SourcedDateValue {
  raw_value: string;
  normalized_value: string | null;
  confidence: number;
  extraction_method: ExtractionMethod;
  sources: SourceEvidence[];
}

export interface PatientInformation {
  name: SourcedTextValue | null;
  date_of_birth: SourcedDateValue | null;
  medical_record_number: SourcedTextValue | null;
}

export interface ProviderInformation {
  name: string;
  role: string | null;
  organization: string | null;
  confidence: number;
  extraction_method: ExtractionMethod;
  sources: SourceEvidence[];
}

export interface DiagnosisInformation {
  name: string;
  code: string | null;
  code_system: string | null;
  status: DiagnosisStatus;
  confidence: number;
  extraction_method: ExtractionMethod;
  sources: SourceEvidence[];
}

export interface MedicationInformation {
  name: string;
  dose: string | null;
  route: string | null;
  frequency: string | null;
  duration: string | null;
  instructions: string | null;
  status: MedicationStatus;
  confidence: number;
  extraction_method: ExtractionMethod;
  sources: SourceEvidence[];
}

export interface LabResultInformation {
  test_name: string;
  raw_value: string;
  numeric_value: number | null;
  unit: string | null;
  reference_range: string | null;
  flag: LabResultFlag;
  collected_at: SourcedDateValue | null;
  confidence: number;
  extraction_method: ExtractionMethod;
  sources: SourceEvidence[];
}

export interface ProcedureInformation {
  name: string;
  procedure_date: SourcedDateValue | null;
  result: string | null;
  confidence: number;
  extraction_method: ExtractionMethod;
  sources: SourceEvidence[];
}

export interface FollowUpInstruction {
  instruction: string;
  timeframe: string | null;
  specialty: string | null;
  confidence: number;
  extraction_method: ExtractionMethod;
  sources: SourceEvidence[];
}

export interface ExtractionWarning {
  code: string;
  message: string;
}

export interface MedicalDocumentExtraction {
  schema_version: "1.0";
  extraction_id: string | null;
  document_id: string;
  document_type: MedicalDocumentType;
  status: ExtractionStatus;
  patient: PatientInformation;
  document_date: SourcedDateValue | null;
  providers: ProviderInformation[];
  diagnoses: DiagnosisInformation[];
  medications: MedicationInformation[];
  lab_results: LabResultInformation[];
  procedures: ProcedureInformation[];
  follow_up_instructions: FollowUpInstruction[];
  warnings: ExtractionWarning[];
  extraction_confidence: number;
  generated_at: string;
}

export interface PersistedMedicalExtraction {
  extraction_id: string;
  document_id: string;
  schema_version: string;
  status: ExtractionStatus;
  extraction_method: ExtractionMethod;
  model_name: string;
  extraction: MedicalDocumentExtraction;
  created_at: string;
  updated_at: string;
}

export interface ExtractionGenerateResponse {
  cached: boolean;
  replaced: boolean;
  message: string;
  result: PersistedMedicalExtraction;
}

export interface ExtractionDeleteResponse {
  document_id: string;
  deleted: boolean;
  message: string;
}