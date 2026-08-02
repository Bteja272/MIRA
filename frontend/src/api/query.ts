import { apiRequest } from "./http";
import type {
  QueryRequest,
  QueryResponse,
} from "../types/query";

export function queryMira(
  request: QueryRequest,
  signal?: AbortSignal,
): Promise<QueryResponse> {
  return apiRequest<QueryResponse>(
    "/query",
    {
      method: "POST",
      body: JSON.stringify(request),
      signal,
    },
  );
}