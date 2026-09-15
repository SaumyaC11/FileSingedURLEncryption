import { useState } from "react";
import "./App.css";
import { UploadForm } from "./components/UploadForm";
import { FileRow } from "./components/FileRow";
import { RetrieveFileForm } from "./components/RetrieveFileForm";
import { StatusCheckForm } from "./components/StatusCheckForm";
import type { TrackedFile } from "./types";

function App() {
  const [userId, setUserId] = useState("");
  const [files, setFiles] = useState<TrackedFile[]>([]);

  function handleUploaded(file: TrackedFile) {
    setFiles((prev) => [file, ...prev]);
  }

  return (
    <main className="app">
      <header className="app-header">
        <div className="badge">📁</div>
        <h1>File Vault</h1>
        <p className="subtitle">Upload a file, generate a signed link, then use it to retrieve the file.</p>
      </header>

      <div className="card">
        <h2><span className="step">1</span> Who are you?</h2>
        <input
          type="text"
          placeholder="Your user ID"
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
        />
      </div>

      <UploadForm userId={userId} onUploaded={handleUploaded} />

      <div className="card">
        <h2><span className="step">3</span> Your files</h2>
        {files.length === 0 ? (
          <p className="empty">No files uploaded yet.</p>
        ) : (
          <ul className="file-list">
            {files.map((file) => (
              <FileRow key={file.fileId} file={file} />
            ))}
          </ul>
        )}
      </div>

      <RetrieveFileForm />

      <StatusCheckForm userId={userId} />
    </main>
  );
}

export default App;
