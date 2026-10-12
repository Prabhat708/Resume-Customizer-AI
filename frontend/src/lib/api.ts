/**
 * src/lib/api.ts — Native fetch client for the Resume Customizer API.
 * Uses native fetch without external HTTP libraries.
 * Handles ErrorResponse parsing and typed error exceptions.
 */

import {
  CustomizeResponse,
  ErrorDetail,
  ErrorResponse,
  HealthResponse,
  TailoredResume,
} from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  public readonly code: string;
  public readonly details?: unknown;
  public readonly status: number;

  constructor(status: number, errorDetail: ErrorDetail) {
    super(errorDetail.message);
    this.name = "ApiError";
    this.status = status;
    this.code = errorDetail.code;
    this.details = errorDetail.details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail: ErrorDetail = {
      code: "INTERNAL_ERROR",
      message: `Request failed with status ${response.status}`,
    };
    try {
      const data = (await response.json()) as ErrorResponse;
      if (data && data.error && data.error.code) {
        errorDetail = data.error;
      }
    } catch {
      // Fallback if response wasn't JSON
    }
    throw new ApiError(response.status, errorDetail);
  }

  return response.json() as Promise<T>;
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/health`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  return handleResponse<HealthResponse>(res);
}

export async function customizeResume(
  file: File,
  jobDescription: string
): Promise<CustomizeResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("job_description", jobDescription);

  const res = await fetch(`${API_BASE_URL}/api/v1/customize`, {
    method: "POST",
    headers: { Accept: "application/json" },
    body: formData,
  });

  return handleResponse<CustomizeResponse>(res);
}

export async function exportTailoredPdf(tailoredResume: TailoredResume): Promise<Blob> {
  const res = await fetch(`${API_BASE_URL}/api/v1/export/pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/pdf",
    },
    body: JSON.stringify({ tailored_resume: tailoredResume }),
  });

  if (!res.ok) {
    let errorDetail: ErrorDetail = {
      code: "EXPORT_FAILED",
      message: "Failed to generate PDF.",
    };
    try {
      const data = (await responseJson(res)) as ErrorResponse;
      if (data?.error?.code) {
        errorDetail = data.error;
      }
    } catch {
      // Non-JSON error
    }
    throw new ApiError(res.status, errorDetail);
  }

  return res.blob();
}

async function responseJson(res: Response): Promise<unknown> {
  return res.json();
}
