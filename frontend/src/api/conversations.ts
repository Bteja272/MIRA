import {
  apiRequest,
} from "./http";

import type {
  ConversationDetailResponse,
  ConversationListResponse,
} from "../types/conversation";


export async function getConversations():
  Promise<ConversationListResponse> {
  return apiRequest<
    ConversationListResponse
  >(
    "/conversations",
  );
}


export async function getConversation(
  conversationId: string,
): Promise<
  ConversationDetailResponse
> {
  return apiRequest<
    ConversationDetailResponse
  >(
    (
      "/conversations/"
      + encodeURIComponent(
        conversationId,
      )
    ),
  );
}


export async function deleteConversation(
  conversationId: string,
): Promise<void> {
  await apiRequest<null>(
    (
      "/conversations/"
      + encodeURIComponent(
        conversationId,
      )
    ),
    {
      method: "DELETE",
    },
  );
}