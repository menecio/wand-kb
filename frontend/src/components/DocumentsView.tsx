import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { deleteDocument, uploadDocuments } from '../lib/api';
import type { DocumentStatus, DocumentSummary, UploadResultItem } from '../types';
import Button from './ui/Button';
import Spinner from './Spinner';
import StatusBadge from './StatusBadge';

interface DocumentsViewProps {
  documents: DocumentSummary[];
  status: 'loading' | 'error' | 'ready';
  onRefresh: () => void;
  onUploaded: (results: UploadResultItem[]) => void;
  onDeleted: (documentId: string) => void;
}

/**
 * Summarize per-file ingestion outcomes from the real contract (§4, §8):
 * ready, processing, failed, already-uploaded (idempotent duplicates), and
 * rejected files. Never claims a new document for a duplicate.
 */
function summarizeUpload(results: UploadResultItem[]): string {
  const parts: string[] = [];
  const byStatus = (status: DocumentStatus) =>
    results.filter((item) => item.status === status);
  const ready = byStatus('READY');
  const processing = byStatus('PROCESSING');
  const failed = byStatus('FAILED');
  const duplicate = byStatus('DUPLICATE');
  const rejected = byStatus('REJECTED');
  const names = (items: UploadResultItem[]) =>
    items.map((item) => item.filename).join(', ');
  const files = (count: number) => (count === 1 ? 'file' : 'files');

  if (ready.length > 0) parts.push(`${ready.length} ${files(ready.length)} ready.`);
  if (processing.length > 0)
    parts.push(`${processing.length} ${files(processing.length)} processing.`);
  if (failed.length > 0)
    parts.push(`${failed.length} ${files(failed.length)} failed: ${names(failed)}.`);
  if (duplicate.length > 0)
    parts.push(
      `${duplicate.length} already uploaded: ${names(duplicate)} — no new document was created.`,
    );
  if (rejected.length > 0)
    parts.push(`${rejected.length} ${files(rejected.length)} rejected: ${names(rejected)}.`);

  return parts.join(' ');
}

export default function DocumentsView({
  documents,
  status,
  onRefresh,
  onUploaded,
  onDeleted,
}: DocumentsViewProps) {
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  async function handleDelete(document: DocumentSummary) {
    setDeleteError(null);
    setDeletingId(document.document_id);
    try {
      await deleteDocument(document.document_id);
      onDeleted(document.document_id);
      setNotice(`${document.document_name} deleted.`);
    } catch {
      setDeleteError(`Could not delete ${document.document_name}. Try again.`);
    } finally {
      setDeletingId(null);
    }
  }

  async function handleUpload(files: File[]) {
    if (files.length === 0) return;
    setUploading(true);
    setNotice(null);
    try {
      const result = await uploadDocuments(files);
      onUploaded(result.results);
      setNotice(summarizeUpload(result.results));
    } catch {
      setNotice('The upload could not be completed. Try again.');
    } finally {
      setUploading(false);
    }
  }

  return (
    <section>
      <h1>Documents</h1>
      <p>Upload files and manage the sources available for search.</p>

      <form
        className="panel upload-form"
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
        <Button type="submit" disabled={uploading}>
          {uploading ? (
            <>
              <Spinner /> Uploading…
            </>
          ) : (
            'Upload documents'
          )}
        </Button>
      </form>

      {deleteError && (
        <div role="alert" className="error-state panel">
          <p>{deleteError}</p>
        </div>
      )}

      {notice && (
        <div role="status" className="notice">
          <p>{notice}</p>
          <Button
            variant="ghost"
            size="sm"
            aria-label="Dismiss notice"
            onClick={() => setNotice(null)}
          >
            Dismiss
          </Button>
        </div>
      )}

      {status === 'error' ? (
        <div role="alert" className="error-state panel">
          <p>Could not load documents.</p>
          <Button variant="outline" onClick={onRefresh}>
            Retry
          </Button>
        </div>
      ) : status === 'loading' ? (
        <p role="status" className="state">
          <Spinner /> Loading documents…
        </p>
      ) : documents.length === 0 ? (
        <p className="state">No sources yet. Upload a document to make it searchable.</p>
      ) : (
        <table className="documents-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Status</th>
              <th>Error</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.document_id}>
                <td className="cell-name">{document.document_name}</td>
                <td>
                  <StatusBadge status={document.status} />
                </td>
                <td className="cell-error">{document.error ?? ''}</td>
                <td>
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label={`Delete ${document.document_name}`}
                    disabled={deletingId === document.document_id}
                    onClick={() => void handleDelete(document)}
                  >
                    {deletingId === document.document_id ? (
                      <Spinner />
                    ) : (
                      <Trash2 aria-hidden="true" />
                    )}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
