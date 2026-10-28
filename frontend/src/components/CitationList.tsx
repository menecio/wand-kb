import { useState } from 'react';
import type { Citation } from '../types';

function formatPages(pageStart: number | null, pageEnd: number | null): string | null {
  if (pageStart == null) return null;
  if (pageEnd != null && pageEnd !== pageStart) return `Pages ${pageStart}–${pageEnd}`;
  return `Page ${pageStart}`;
}

export default function CitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;

  return (
    <section aria-label="Evidence">
      <h2>Evidence</h2>
      <ul>
        {citations.map((citation) => (
          <CitationItem key={citation.chunk_id} citation={citation} />
        ))}
      </ul>
    </section>
  );
}

function CitationItem({ citation }: { citation: Citation }) {
  const [open, setOpen] = useState(false);
  const pages = formatPages(citation.page_start, citation.page_end);

  return (
    <li>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        {citation.document_name}
        {pages ? ` · ${pages}` : ''}
      </button>
      {open && (
        <div>
          {citation.section && <p>{citation.section}</p>}
          <blockquote>{citation.excerpt}</blockquote>
          <p>
            <span>Retrieval score</span>{' '}
            <span>{citation.relevance_score.toFixed(2)}</span>
          </p>
        </div>
      )}
    </li>
  );
}
