import {
  ApiError,
  apiRequest,
} from "./http";
import type {
  ExtractionDeleteResponse,
  ExtractionGenerateResponse,
  PersistedMedicalExtraction,
} from "../types/extractions";

export function generateExtraction(
  documentId: string,
  replaceExisting = false,
): Promise<ExtractionGenerateResponse> {
  return apiRequest<ExtractionGenerateResponse>(
    `/documents/${encodeURIComponent(
      documentId,
    )}/extract`,
    {
      method: "POST",
      body: JSON.stringify({
        replace_existing: replaceExisting,
      }),
    },
  );
}

export function getExtraction(
  documentId: string,
): Promise<PersistedMedicalExtraction> {
  return apiRequest<PersistedMedicalExtraction>(
    `/documents/${encodeURIComponent(
      documentId,
    )}/extraction`,
  );
}

export async function getExtractionOrNull(
  documentId: string,
): Promise<PersistedMedicalExtraction | null> {
  try {
    return await getExtraction(documentId);
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

export function deleteExtraction(
  documentId: string,
): Promise<ExtractionDeleteResponse> {
  return apiRequest<ExtractionDeleteResponse>(
    `/documents/${encodeURIComponent(
      documentId,
    )}/extraction`,
    {
      method: "DELETE",
    },
  );
}