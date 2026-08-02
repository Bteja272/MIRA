export interface QueryRequest {
  query: string;
  document_ids?: string[];
}

export type QuerySource = Record<string, unknown>;

export interface QueryResponse {
  query: string;
  answer: string | null;
  route: string;
  document_id: string | null;
  document_ids: string[];
  selected_document_count: number;
  sources: QuerySource[];
  safety_category?: string | null;
  [key: string]: unknown;
}