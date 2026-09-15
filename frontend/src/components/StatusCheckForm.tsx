import { useState } from "react";
import type { FormEvent } from "react";
import { getFileStatus } from "../api/fileService";
import type { FileStatusResponse } from "../api/fileService";

function formatBytes(byteLength: number): string {
  if (byteLength < 1024) return `${byteLength} B`;
  const units = ["KB", "MB", "GB"];
  let value = byteLength / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

interface StatusCheckFormProps {
  userId: string;
}

export function StatusCheckForm({ userId }: StatusCheckFormProps) {
  const [fileId, setFileId] = useState("");
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<FileStatusResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!fileId.trim()) {
      setError("Enter a file ID first.");
      return;
    }
    if (!userId.trim()) {
      setError("Enter your user ID above first.");
      return;
    }

    setIsChecking(true);
    setError(null);
    setStatus(null);
    try {
      const result = await getFileStatus(fileId.trim(), userId);
      setStatus(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not fetch file status.");
    } finally {
      setIsChecking(false);
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2><span className="step">5</span> Check file status</h2>
      <label htmlFor="status-file-id-input">File ID</label>
      <input
        id="status-file-id-input"
        type="text"
        placeholder="Paste a file ID here"
        value={fileId}
        onChange={(event) => {
          setFileId(event.target.value);
          setError(null);
        }}
        disabled={isChecking}
      />
      <button type="submit" disabled={isChecking}>
        {isChecking ? "Checking..." : "Check status"}
      </button>
      {error && <p className="error">{error}</p>}

      {status && (
        <div className="status-result">
          <div className="status-row">
            <span className="status-label">Filename</span>
            <span>{status.filename}</span>
          </div>
          <div className="status-row">
            <span className="status-label">Size</span>
            <span>{formatBytes(status.byte_length)}</span>
          </div>
          <div className="status-row">
            <span className="status-label">Uploaded</span>
            <span>{new Date(status.uploaded_at).toLocaleString()}</span>
          </div>
          <div className="status-row">
            <span className="status-label">Active signed URL</span>
            <span>{status.signed_url ? "Yes" : "None"}</span>
          </div>
          {status.signed_url && (
            <div className="signed-url-text">{status.signed_url}</div>
          )}
        </div>
      )}
    </form>
  );
}
