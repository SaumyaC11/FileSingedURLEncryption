import { useState } from "react";
import type { FormEvent } from "react";
import { generateSignedUrl, uploadFile } from "../api/fileService";
import { TTL_PRESETS } from "../constants";
import type { TrackedFile } from "../types";

interface UploadFormProps {
  userId: string;
  onUploaded: (file: TrackedFile) => void;
}

// Renders a form that uploads a file and immediately requests a signed URL for it.
export function UploadForm({ userId, onUploaded }: UploadFormProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ttlSeconds, setTtlSeconds] = useState(TTL_PRESETS[0].seconds);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Uploads the selected file, then generates a signed URL for it, reporting the result.
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;

    if (!selectedFile) {
      setError("Choose a file first.");
      return;
    }
    if (!userId.trim()) {
      setError("Enter a user ID first.");
      return;
    }

    setIsUploading(true);
    setError(null);
    try {
      const { file_id } = await uploadFile(userId, selectedFile);
      const trackedFile: TrackedFile = { fileId: file_id, filename: selectedFile.name };

      try {
        const signed = await generateSignedUrl(file_id, ttlSeconds, userId);
        trackedFile.signedUrl = signed.signed_url;
        trackedFile.expiresAt = signed.expires_at;
      } catch (err) {
        trackedFile.error =
          err instanceof Error ? err.message : "File uploaded, but the signed URL could not be created.";
      }

      onUploaded(trackedFile);
      setSelectedFile(null);
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2><span className="step">2</span> Upload a file</h2>
      <label className={`file-drop${selectedFile ? " has-file" : ""}`}>
        <span>{selectedFile ? `📄 ${selectedFile.name}` : "⬆️ Click to choose a file"}</span>
        <input
          type="file"
          onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
          disabled={isUploading}
        />
      </label>

      <div>
        <label htmlFor="ttl-select">Signed link expires in</label>
        <select
          id="ttl-select"
          value={ttlSeconds}
          onChange={(event) => setTtlSeconds(Number(event.target.value))}
          disabled={isUploading}
        >
          {TTL_PRESETS.map((preset) => (
            <option key={preset.seconds} value={preset.seconds}>
              {preset.label}
            </option>
          ))}
        </select>
      </div>

      <button type="submit" disabled={isUploading}>
        {isUploading ? "Uploading..." : "Upload"}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
