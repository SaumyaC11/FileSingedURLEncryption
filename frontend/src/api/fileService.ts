const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001";

export interface UploadResponse {
  file_id: string;
}

export interface GenerateSignedUrlResponse {
  signed_url: string;
  expires_at: string;
}

export interface FileStatusResponse {
  filename: string;
  byte_length: number;
  uploaded_at: string;
  signed_url: string | null;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return typeof body?.detail === "string" ? body.detail : response.statusText;
  } catch {
    return response.statusText;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json() as Promise<T>;
}

export function uploadFile(userId: string, file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("user_id", userId);
  formData.append("file", file);

  return requestJson<UploadResponse>("/v1/upload", {
    method: "POST",
    body: formData,
  });
}

export function generateSignedUrl(
  fileId: string,
  ttlSeconds: number,
  requestingUserId: string,
): Promise<GenerateSignedUrlResponse> {
  return requestJson<GenerateSignedUrlResponse>("/v1/generateSignedURL", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      file_id: fileId,
      ttl_seconds: ttlSeconds,
      requesting_user_id: requestingUserId,
    }),
  });
}

export function getFileStatus(
  fileId: string,
  requestingUserId: string,
): Promise<FileStatusResponse> {
  const params = new URLSearchParams({ requesting_user_id: requestingUserId });
  return requestJson<FileStatusResponse>(`/v1/status/${fileId}?${params.toString()}`);
}
