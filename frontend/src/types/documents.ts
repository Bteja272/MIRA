export interface DocumentSummary {
  document_id: string;
  filename: string;
  document_type: string | null;
  file_size_bytes: number | null;
  chunk_count: number;
  uploaded_at: string | null;
}

export interface DocumentDetail
  extends DocumentSummary {
  source: string | null;
  file_hash: string | null;
}

export interface DocumentListResponse {
  documents: DocumentSummary[];
  count: number;
}

export interface DocumentDeleteResponse {
  document_id: string;
  filename: string;
  deleted: boolean;
  file_deleted: boolean;
}

export interface IngestResponse {
  duplicate: boolean;
  document_id: string | null;
  existing_document_id: string | null;
  filename: string;
  document_type: string | null;
  file_size_bytes: number | null;
  chunks_indexed: number | null;
  message: string;
  development_notice: string | null;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}