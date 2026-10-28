import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import type { Citation } from '../types';

function formatPages(pageStart: number | null, pageEnd: number | null): string | null {
  if (pageStart == null) return null;
  if (pageEnd != null && pageEnd !== pageStart) return `Pages ${pageStart}–${pageEnd}`;
  return `Page ${pageStart}`;
}

interface CitationListProps {
  citations: Citation[];
}

/**
 * Evidence list (§12): heading shows the returned source count, the first
 * citation opens by default, and C1/C2 are presentational labels derived from
 * order — chunk_id remains the real identity.
 */
export default function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) return null;

  const sourceWord = citations.length === 1 ? 'source' : 'sources';

  return (
    <section aria-label="Evidence" className="evidence panel">
      <h2 className="evidence-heading">
        Evidence{' '}
        <span className="evidence-count">
          {citations.length} {sourceWord}
        </span>
      </h2>
      <ul className="citations">
        {citations.map((citation, index) => (
          <CitationItem
            key={citation.chunk_id}
            citation={citation}
            label={`C${index + 1}`}
            defaultOpen={index === 0}
          />
        ))}
      </ul>
    </section>
  );
}

interface CitationItemProps {
  citation: Citation;
  label: string;
  defaultOpen: boolean;
}

function CitationItem({ citation, label, defaultOpen }: CitationItemProps) {
  const [open, setOpen] = useState(defaultOpen);
  const pages = formatPages(citation.page_start, citation.page_end);

  return (
    <li className="citation">
      <button
        type="button"
        className="citation-toggle"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="citation-label">{label}</span>
        <span className="citation-name">{citation.document_name}</span>
        {pages && <span>{pages}</span>}
        <ChevronDown size={16} aria-hidden="true" className="citation-chevron" />
      </button>
      {open && (
        <div className="citation-body">
          {citation.section && <p className="citation-section">{citation.section}</p>}
          <blockquote className="citation-excerpt">{citation.excerpt}</blockquote>
          <p className="retrieval-score">
            Retrieval score <strong>{citation.relevance_score.toFixed(2)}</strong>
          </p>
        </div>
      )}
    </li>
  );
}
