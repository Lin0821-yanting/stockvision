import type { ApiErrorBody } from "@/types/api";

export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown>;

  constructor({
    status,
    code,
    message,
    details = {},
  }: {
    status: number;
    code: string;
    message: string;
    details?: Record<string, unknown>;
  }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }

  /** 後端沒有啟動或網路中斷 */
  get isNetworkError() {
    return this.status === 0;
  }
}

type QueryValue = string | number | boolean | null | undefined;

export type RequestOptions = Omit<RequestInit, "body"> & {
  json?: unknown;
  query?: Record<string, QueryValue>;
};

export async function apiRequest<T>(path: string, { json, query, headers, ...init }: RequestOptions = {}): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
      body: json !== undefined ? JSON.stringify(json) : undefined,
      cache: "no-store",
    });
  } catch {
    throw new ApiError({
      status: 0,
      code: "NETWORK_ERROR",
      message: `無法連線到 StockVision 後端（${API_BASE_URL}），請確認 Python FastAPI 服務已啟動。`,
    });
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = null;
    }
  }

  if (!response.ok) {
    const error = (body as Partial<ApiErrorBody> | null)?.error;
    throw new ApiError({
      status: response.status,
      code: error?.code ?? `HTTP_${response.status}`,
      message: error?.message ?? `請求失敗（HTTP ${response.status}）`,
      details: error?.details ?? {},
    });
  }

  if (body === null) {
    throw new ApiError({ status: response.status, code: "INVALID_RESPONSE", message: "後端回傳的資料格式不正確" });
  }
  return body as T;
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "發生未預期的錯誤";
}
