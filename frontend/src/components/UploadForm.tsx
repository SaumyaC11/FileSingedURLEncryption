import { useState } from "react";
import type { FormEvent } from "react";
import { uploadFile } from "../api/fileService";
import type { TrackedFile } from "../types";

interface UploadFormProps {
  userId: string;
  onUploaded: (file: TrackedFile) => void;
}

export function UploadForm({ userId, onUploaded }: UploadFormProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      onUploaded({ fileId: file_id, filename: selectedFile.name });
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
      <button type="submit" disabled={isUploading}>
        {isUploading ? "Uploading..." : "Upload"}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
