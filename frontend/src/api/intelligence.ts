import {
  ApiError,
  apiRequest,
} from "./http";

import type {
  IntelligenceCompareResponse,
  IntelligenceDeleteResponse,
  IntelligenceGenerateResponse,
  IntelligenceTimelineResponse,
  PersistedMedicalIntelligence,
} from "../types/intelligence";

export function generateIntelligence(
  documentId: string,
  replaceExisting = false,
): Promise<IntelligenceGenerateResponse> {
  return apiRequest<IntelligenceGenerateResponse>(
    `/documents/${encodeURIComponent(
      documentId,
    )}/intelligence`,
    {
      method: "POST",
      body: JSON.stringify({
        replace_existing: replaceExisting,
      }),
    },
  );
}

export function getIntelligence(
  documentId: string,
): Promise<PersistedMedicalIntelligence> {
  return apiRequest<PersistedMedicalIntelligence>(
    `/documents/${encodeURIComponent(
      documentId,
    )}/intelligence`,
  );
}

export async function getIntelligenceOrNull(
  documentId: string,
): Promise<PersistedMedicalIntelligence | null> {
  try {
    return await getIntelligence(
      documentId,
    );
  } catch (error) {
    if (
      error instanceof ApiError
      && error.status === 404
    ) {
      return null;
    }

    throw error;
  }
}

export function deleteIntelligence(
  documentId: string,
): Promise<IntelligenceDeleteResponse> {
  return apiRequest<IntelligenceDeleteResponse>(
    `/documents/${encodeURIComponent(
      documentId,
    )}/intelligence`,
    {
      method: "DELETE",
    },
  );
}

export function buildMedicalTimeline(
  documentIds: string[],
): Promise<IntelligenceTimelineResponse> {
  return apiRequest<IntelligenceTimelineResponse>(
    "/intelligence/timeline",
    {
      method: "POST",
      body: JSON.stringify({
        document_ids: documentIds,
      }),
    },
  );
}

export function compareMedicalDocuments(
  documentIds: string[],
): Promise<IntelligenceCompareResponse> {
  return apiRequest<IntelligenceCompareResponse>(
    "/intelligence/compare",
    {
      method: "POST",
      body: JSON.stringify({
        document_ids: documentIds,
      }),
    },
  );
}