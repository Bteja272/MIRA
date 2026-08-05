import {
  API_BASE_URL,
  ApiError,
  apiRequest,
  extractApiErrorMessage,
} from "./http";
import {
  clearAccessToken,
  getAccessToken,
  notifyUnauthorized,
} from "../auth/tokenStorage";
import type {
  DocumentDeleteResponse,
  DocumentDetail,
  DocumentListResponse,
  IngestResponse,
  UploadProgress,
} from "../types/documents";

export function getDocuments():
  Promise<DocumentListResponse> {
  return apiRequest<DocumentListResponse>(
    "/documents",
  );
}

export function getDocument(
  documentId: string,
): Promise<DocumentDetail> {
  return apiRequest<DocumentDetail>(
    `/documents/${encodeURIComponent(
      documentId,
    )}`,
  );
}

export function deleteDocument(
  documentId: string,
): Promise<DocumentDeleteResponse> {
  return apiRequest<DocumentDeleteResponse>(
    `/documents/${encodeURIComponent(
      documentId,
    )}`,
    {
      method: "DELETE",
    },
  );
}

function parseXhrBody(
  xhr: XMLHttpRequest,
): unknown {
  const contentType =
    xhr.getResponseHeader(
      "content-type",
    ) ?? "";

  if (
    contentType.includes(
      "application/json",
    )
  ) {
    try {
      return JSON.parse(
        xhr.responseText,
      ) as unknown;
    } catch {
      return xhr.responseText;
    }
  }

  return xhr.responseText;
}

export function uploadDocument(
  file: File,
  onProgress?: (
    progress: UploadProgress,
  ) => void,
): Promise<IngestResponse> {
  return new Promise(
    (resolve, reject) => {
      const xhr =
        new XMLHttpRequest();

      xhr.open(
        "POST",
        `${API_BASE_URL}/ingest`,
      );

      xhr.setRequestHeader(
        "Accept",
        "application/json",
      );

      const token = getAccessToken();

      if (token) {
        xhr.setRequestHeader(
          "Authorization",
          `Bearer ${token}`,
        );
      }

      xhr.upload.addEventListener(
        "progress",
        (event) => {
          if (
            !event.lengthComputable
            || !onProgress
          ) {
            return;
          }

          const percentage = Math.min(
            100,
            Math.round(
              (
                event.loaded
                / event.total
              ) * 100,
            ),
          );

          onProgress({
            loaded: event.loaded,
            total: event.total,
            percentage,
          });
        },
      );

      xhr.addEventListener(
        "load",
        () => {
          const body =
            parseXhrBody(xhr);

          if (
            xhr.status >= 200
            && xhr.status < 300
          ) {
            resolve(
              body as IngestResponse,
            );
            return;
          }

          if (
            xhr.status === 401
            && token
          ) {
            clearAccessToken();
            notifyUnauthorized(
              "unauthorized",
            );
          }

          reject(
            new ApiError(
              extractApiErrorMessage(
                body,
                (
                  "Upload failed with status "
                  + xhr.status
                  + "."
                ),
              ),
              xhr.status,
              body,
            ),
          );
        },
      );

      xhr.addEventListener(
        "error",
        () => {
          reject(
            new ApiError(
              "The MIRA API could not be reached.",
              0,
              null,
            ),
          );
        },
      );

      xhr.addEventListener(
        "abort",
        () => {
          reject(
            new ApiError(
              "The upload was cancelled.",
              0,
              null,
            ),
          );
        },
      );

      const formData =
        new FormData();

      formData.append(
        "file",
        file,
        file.name,
      );

      xhr.send(formData);
    },
  );
}