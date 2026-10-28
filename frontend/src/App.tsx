import { useCallback, useEffect, useState } from 'react';
import { listDocuments } from './lib/api';
import type { DocumentStatus, DocumentSummary } from './types';
import DocumentsView from './components/DocumentsView';
import QueryView from './components/QueryView';

type View = 'ask' | 'documents';
type LoadStatus = 'loading' | 'ready' | 'error';

interface UploadedRow {
  document_id: string;
  document_name: string;
  status: DocumentStatus;
  error: string | null;
}

export default function App() {
  const [view, setView] = useState<View>('ask');
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [status, setStatus] = useState<LoadStatus>('loading');

  const load = useCallback(async () => {
    setStatus('loading');
    try {
      const data = await listDocuments();
      setDocuments(data.documents);
      setStatus('ready');
    } catch {
      setStatus('error');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const hasReady = documents.some((document) => document.status === 'READY');

  function handleUploaded(rows: UploadedRow[]) {
    const appended: DocumentSummary[] = rows.map((row) => ({
      document_id: row.document_id,
      document_name: row.document_name,
      content_sha256: '',
      status: row.status,
      error: row.error,
      created_at: '',
    }));
    setDocuments((previous) => [...previous, ...appended]);
    setStatus('ready');
  }

  return (
    <main>
      <nav aria-label="Primary">
        <a
          href="#ask"
          aria-current={view === 'ask' ? 'page' : undefined}
          onClick={(event) => {
            event.preventDefault();
            setView('ask');
          }}
        >
          Ask &amp; answers
        </a>
        <a
          href="#documents"
          aria-current={view === 'documents' ? 'page' : undefined}
          onClick={(event) => {
            event.preventDefault();
            setView('documents');
          }}
        >
          Documents
        </a>
      </nav>

      {view === 'ask' ? (
        <QueryView hasReady={hasReady} />
      ) : (
        <DocumentsView
          documents={documents}
          status={status}
          onRefresh={() => void load()}
          onUploaded={handleUploaded}
        />
      )}
    </main>
  );
}
