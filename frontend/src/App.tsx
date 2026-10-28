import { useCallback, useEffect, useState } from 'react';
import { listDocuments } from './lib/api';
import type { DocumentSummary, UploadResultItem } from './types';
import DocumentsView from './components/DocumentsView';
import QueryView from './components/QueryView';

type View = 'ask' | 'documents';
type LoadStatus = 'loading' | 'ready' | 'error';

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

  /**
   * Reconcile uploaded rows with the current list by document_id (§4, J8):
   * update existing rows in place, append genuinely new ones. Rejected
   * uploads carry no document_id and no registry row, so they are reported
   * per-file in the upload notice instead of being added with a fabricated id.
   */
  function handleUploaded(results: UploadResultItem[]) {
    setDocuments((previous) => {
      const next = [...previous];
      for (const item of results) {
        if (item.document_id === null) continue;
        const index = next.findIndex(
          (document) => document.document_id === item.document_id,
        );
        // The upload contract returns no hash/date: existing rows keep their
        // values and appended rows use placeholders that are never rendered.
        const summary: DocumentSummary = {
          document_id: item.document_id,
          document_name: item.filename,
          content_sha256: index === -1 ? '' : next[index].content_sha256,
          status: item.status,
          error: item.error,
          created_at: index === -1 ? '' : next[index].created_at,
        };
        if (index === -1) {
          next.push(summary);
        } else {
          next[index] = summary;
        }
      }
      return next;
    });
    setStatus('ready');
  }

  return (
    <div className="shell">
      <header className="topbar">
        <a
          className="brand"
          href="#ask"
          onClick={(event) => {
            event.preventDefault();
            setView('ask');
          }}
        >
          Knowledge base
        </a>
        <nav className="topbar-nav" aria-label="Primary">
          <a
            className="nav-link"
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
            className="nav-link"
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
      </header>

      <main className="content">
        {view === 'ask' ? (
          <QueryView hasReady={hasReady} onNavigateToDocuments={() => setView('documents')} />
        ) : (
          <DocumentsView
            documents={documents}
            status={status}
            onRefresh={() => void load()}
            onUploaded={handleUploaded}
          />
        )}
      </main>
    </div>
  );
}
