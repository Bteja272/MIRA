import type {
  QuerySource,
} from "./query";


export type ConversationRole =
  "user" | "assistant";


export interface ConversationMessage {
  message_id: string;

  role: ConversationRole;

  content: string;

  route: string | null;

  document_ids: string[];

  sources: QuerySource[];

  safety_category:
    string | null;

  created_at: string;
}


export interface ConversationSummary {
  conversation_id: string;

  title: string;

  message_count: number;

  created_at: string;

  updated_at: string;
}


export interface ConversationListResponse {
  conversations:
    ConversationSummary[];
}


export interface ConversationDetailResponse {
  conversation_id: string;

  title: string;

  created_at: string;

  updated_at: string;

  messages:
    ConversationMessage[];
}