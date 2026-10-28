import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

export type DocStatus =
  | 'PROCESSING'
  | 'READY'
  | 'FAILED'
  | 'REJECTED'
  | 'DUPLICATE';

export interface DocumentSummaryFixture {
  document_id: string;
  document_name: string;
  content_sha256: string;
  status: DocStatus;
  error: string | null;
  created_at: string;
}

export interface EnrichmentSuggestionFixture {
  action_type: 'UPLOAD_DOCUMENT' | 'QUERY_EXTERNAL_SYSTEM' | 'ASK_USER';
  target: string;
  reason: string;
  suggested_query: string | null;
}

export interface CitationFixture {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_start: number | null;
  page_end: number | null;
  section: string | null;
  excerpt: string;
  relevance_score: number;
}

export interface QueryResponseFixture {
  response_id: string;
  answer: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT_DATA';
  is_complete: boolean;
  missing_info: string[];
  enrichment_suggestions: EnrichmentSuggestionFixture[];
  citations: CitationFixture[];
}

export function makeDocument(
  overrides: Partial<DocumentSummaryFixture> = {},
): DocumentSummaryFixture {
  return {
    document_id: 'doc-1',
    document_name: 'policy.md',
    content_sha256: 'abc123',
    status: 'READY',
    error: null,
    created_at: '2026-10-28T00:00:00Z',
    ...overrides,
  };
}

export function makeQueryResponse(
  overrides: Partial<QueryResponseFixture> = {},
): QueryResponseFixture {
  return {
    response_id: 'resp-1',
    answer: 'The handbook requires two weeks notice.',
    confidence: 'HIGH',
    is_complete: true,
    missing_info: [],
    enrichment_suggestions: [],
    citations: [
      {
        chunk_id: 'chunk-1',
        document_id: 'doc-1',
        document_name: 'policy.md',
        page_start: 2,
        page_end: 2,
        section: 'Resignation',
        excerpt: 'Employees must provide two weeks notice.',
        relevance_score: 0.92345,
      },
    ],
    ...overrides,
  };
}

export function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

export function installFetch(): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn();
  globalThis.fetch = fetchMock as unknown as typeof fetch;
  return fetchMock;
}
