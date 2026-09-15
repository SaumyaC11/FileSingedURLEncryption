import { useState } from "react";
import type { TrackedFile } from "../types";

interface FileRowProps {
  file: TrackedFile;
}

export function FileRow({ file }: FileRowProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (!file.signedUrl) return;
    try {
      await navigator.clipboard.writeText(file.signedUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <li className="file-row">
      <div className="file-row-header">
        <strong>{file.filename}</strong>
        <code>{file.fileId}</code>
      </div>

      {file.error && <p className="error">{file.error}</p>}

      {file.signedUrl && (
        <div className="signed-url-result">
          <div className="signed-url-text">{file.signedUrl}</div>
          <div className="file-row-controls">
            <button type="button" onClick={handleCopy}>
              {copied ? "Copied!" : "Copy signed URL"}
            </button>
            {file.expiresAt && (
              <span className="expires-at">
                Expires: {new Date(file.expiresAt).toLocaleString()}
              </span>
            )}
          </div>
        </div>
      )}
    </li>
  );
}
