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

// Extracts a human-readable error message from a failed response body.
async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return typeof body?.detail === "string" ? body.detail : response.statusText;
  } catch {
    return response.statusText;
  }
}

// Fetches a JSON API endpoint, throwing an ApiError on a non-OK response.
async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }
  return response.json() as Promise<T>;
}

// Uploads a file for a user and returns the assigned file ID.
export function uploadFile(userId: string, file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("user_id", userId);
  formData.append("file", file);

  return requestJson<UploadResponse>("/v1/upload", {
    method: "POST",
    body: formData,
  });
}

// Requests a time-limited signed URL for a file on behalf of its owner.
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

// Fetches a file's metadata and active signed URL status for a given user.
export function getFileStatus(
  fileId: string,
  requestingUserId: string,
): Promise<FileStatusResponse> {
  const params = new URLSearchParams({ requesting_user_id: requestingUserId });
  return requestJson<FileStatusResponse>(`/v1/status/${fileId}?${params.toString()}`);
}

export interface RetrievedFile {
  blob: Blob;
  filename: string;
}

// RFC 5987 form, used whenever the filename isn't URL-safe (spaces, unicode, etc.):
// e.g. filename*=utf-8''My%20Report%20%28final%29.pdf
const FILENAME_STAR = /filename\*=[^']*''([^;]+)/i;
// Simple form, used only when the filename is already URL-safe: filename="report.pdf"
const FILENAME_QUOTED = /filename="([^"]+)"/i;
const FILENAME_BARE = /filename=([^;]+)/i;

// Extracts the filename from a response's Content-Disposition header.
function filenameFromResponse(response: Response): string {
  const header = response.headers.get("Content-Disposition") ?? "";

  const starMatch = header.match(FILENAME_STAR);
  if (starMatch) {
    try {
      return decodeURIComponent(starMatch[1].trim());
    } catch {
      return starMatch[1].trim();
    }
  }

  const quotedMatch = header.match(FILENAME_QUOTED);
  if (quotedMatch) return quotedMatch[1];

  const bareMatch = header.match(FILENAME_BARE);
  if (bareMatch) return bareMatch[1].trim();

  return "download";
}

const SIGNED_URL_PATTERN = /^https?:\/\/.+\/v1\/returnFile\?.*token=.+/i;

// Checks whether a string looks like a valid return-file signed URL.
export function isSignedUrl(value: string): boolean {
  return SIGNED_URL_PATTERN.test(value.trim());
}

// Downloads the file behind a signed URL, mapping error statuses to friendly messages.
export async function retrieveFile(signedUrl: string): Promise<RetrievedFile> {
  if (!isSignedUrl(signedUrl)) {
    throw new ApiError(
      "That doesn't look like a signed URL. Paste the full link you received (not a file ID).",
      0,
    );
  }

  let response: Response;
  try {
    response = await fetch(signedUrl);
  } catch {
    throw new ApiError("Could not reach the file service. Check the URL and try again.", 0);
  }

  if (response.status === 401) {
    throw new ApiError("This signed URL is invalid.", response.status);
  }
  if (response.status === 410) {
    throw new ApiError("This signed URL has expired. Its TTL is no longer valid.", response.status);
  }
  if (response.status === 404) {
    throw new ApiError("The file behind this URL no longer exists.", response.status);
  }
  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }

  return { blob: await response.blob(), filename: filenameFromResponse(response) };
}
