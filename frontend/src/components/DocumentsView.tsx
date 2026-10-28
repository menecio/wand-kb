import { useState } from 'react';
import { uploadDocuments } from '../lib/api';
import type { DocumentStatus, DocumentSummary } from '../types';
import StatusBadge from './StatusBadge';

interface Row {
  document_id: string;
  document_name: string;
  status: DocumentStatus;
  error: string | null;
}

interface DocumentsViewProps {
  documents: DocumentSummary[];
  status: 'loading' | 'ready' | 'error';
  onRefresh: () => void;
  onUploaded: (rows: Row[]) => void;
}

export default function DocumentsView({
  documents,
  status,
  onRefresh,
  onUploaded,
}: DocumentsViewProps) {
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function handleUpload(files: File[]) {
    if (files.length === 0) return;
    setUploading(true);
    setNotice(null);
    try {
      const result = await uploadDocuments(files);
      onUploaded(
        result.results.map((item) => ({
          document_id: item.document_id ?? `upload-${item.filename}`,
          document_name: item.filename,
          status: item.status,
          error: item.error,
        })),
      );
      setNotice('Upload complete.');
    } catch {
      setNotice('The upload could not be completed.');
    } finally {
      setUploading(false);
    }
  }

  return (
    <section>
      <h1>Documents</h1>
      <p>Upload files and manage the sources available for search.</p>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          const input = event.currentTarget.elements.namedItem(
            'documents',
          ) as HTMLInputElement;
          void handleUpload(Array.from(input.files ?? []));
        }}
      >
        <label htmlFor="documents">Upload documents</label>
        <input
          id="documents"
          name="documents"
          type="file"
          multiple
          accept=".pdf,.md,.txt"
        />
        <button type="submit" disabled={uploading}>
          {uploading ? 'Uploading…' : 'Upload documents'}
        </button>
      </form>

      {notice && (
        <div role="status">
          <span>{notice}</span>
          <button
            type="button"
            onClick={() => setNotice(null)}
            aria-label="Dismiss notice"
          >
            Dismiss
          </button>
        </div>
      )}

      {status === 'error' ? (
        <div>
          <p>Could not load documents.</p>
          <button type="button" onClick={onRefresh}>
            Retry
          </button>
        </div>
      ) : documents.length === 0 ? (
        <p>No sources yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Document</th>
              <th>Status</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.document_id}>
                <td>{document.document_name}</td>
                <td>
                  <StatusBadge status={document.status} />
                </td>
                <td>{document.error ?? ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
