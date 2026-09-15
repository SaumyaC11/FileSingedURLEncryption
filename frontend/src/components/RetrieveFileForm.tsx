import { useState } from "react";
import type { FormEvent } from "react";
import { retrieveFile } from "../api/fileService";

function triggerBrowserDownload(blob: Blob, filename: string) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(objectUrl);
}

export function RetrieveFileForm() {
  const [signedUrl, setSignedUrl] = useState("");
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!signedUrl.trim()) {
      setError("Paste a signed URL first.");
      return;
    }

    setIsDownloading(true);
    setError(null);
    setSuccess(null);
    try {
      const { blob, filename } = await retrieveFile(signedUrl.trim());
      triggerBrowserDownload(blob, filename);
      setSuccess(`Downloaded "${filename}".`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not download the file.");
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2><span className="step">4</span> Retrieve a file</h2>
      <label htmlFor="signed-url-input">Signed URL</label>
      <input
        id="signed-url-input"
        type="text"
        placeholder="Paste a signed URL here"
        value={signedUrl}
        onChange={(event) => {
          setSignedUrl(event.target.value);
          setError(null);
          setSuccess(null);
        }}
        disabled={isDownloading}
      />
      <button type="submit" disabled={isDownloading}>
        {isDownloading ? "Checking link..." : "Download file"}
      </button>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </form>
  );
}
