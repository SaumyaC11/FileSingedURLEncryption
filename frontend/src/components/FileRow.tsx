import { useState } from "react";
import { generateSignedUrl } from "../api/fileService";
import type { TrackedFile } from "../types";

const TTL_PRESETS = [
  { label: "1 hour", seconds: 3600 },
  { label: "1 day", seconds: 86400 },
  { label: "7 days", seconds: 604800 },
];

interface FileRowProps {
  userId: string;
  file: TrackedFile;
  onChange: (fileId: string, patch: Partial<TrackedFile>) => void;
}

export function FileRow({ userId, file, onChange }: FileRowProps) {
  const [ttlSeconds, setTtlSeconds] = useState(TTL_PRESETS[0].seconds);
  const [isGenerating, setIsGenerating] = useState(false);

  async function handleGenerate() {
    setIsGenerating(true);
    onChange(file.fileId, { error: undefined });
    try {
      const result = await generateSignedUrl(file.fileId, ttlSeconds, userId);
      onChange(file.fileId, {
        signedUrl: result.signed_url,
        expiresAt: result.expires_at,
      });
    } catch (err) {
      onChange(file.fileId, {
        error: err instanceof Error ? err.message : "Could not generate signed URL.",
      });
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <li className="file-row">
      <div className="file-row-header">
        <strong>{file.filename}</strong>
        <code>{file.fileId}</code>
      </div>

      <div className="file-row-controls">
        <select
          value={ttlSeconds}
          onChange={(event) => setTtlSeconds(Number(event.target.value))}
          disabled={isGenerating}
        >
          {TTL_PRESETS.map((preset) => (
            <option key={preset.seconds} value={preset.seconds}>
              {preset.label}
            </option>
          ))}
        </select>
        <button onClick={handleGenerate} disabled={isGenerating}>
          {isGenerating ? "Generating..." : "Get signed URL"}
        </button>
      </div>

      {file.error && <p className="error">{file.error}</p>}

      {file.signedUrl && (
        <div className="signed-url-result">
          <a href={file.signedUrl} target="_blank" rel="noreferrer">
            Download / open file
          </a>
          {file.expiresAt && (
            <span className="expires-at">
              Expires: {new Date(file.expiresAt).toLocaleString()}
            </span>
          )}
        </div>
      )}
    </li>
  );
}
