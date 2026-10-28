import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import App from './App';
import {
  installFetch,
  jsonResponse,
  makeDocument,
  makeQueryResponse,
  type DocumentSummaryFixture,
  type QueryResponseFixture,
} from './test/fixtures';

function mockDocuments(fetchMock: ReturnType<typeof installFetch>, documents: DocumentSummaryFixture[]) {
  fetchMock.mockResolvedValueOnce(jsonResponse({ documents }));
}

function mockQuery(fetchMock: ReturnType<typeof installFetch>, response: QueryResponseFixture) {
  fetchMock.mockResolvedValueOnce(jsonResponse(response));
}

describe('App — shell and documents', () => {
  let fetchMock: ReturnType<typeof installFetch>;

  beforeEach(() => {
    fetchMock = installFetch();
  });

  it('renders navigation with Ask & answers active by default', () => {
    mockDocuments(fetchMock, [makeDocument()]);
    render(<App />);

    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /ask & answers/i })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('link', { name: /^Documents$/ })).toBeInTheDocument();
  });

  it('fetches the document list on mount and does not auto-query', async () => {
    mockDocuments(fetchMock, []);
    render(<App />);

    await waitFor(() =>
      expect(fetchMock.mock.calls.map((c) => String(c[0]))).toContain('/api/documents'),
    );
    expect(fetchMock.mock.calls.map((c) => String(c[0]))).not.toContain('/api/query');
  });

  it('renders document rows with backend statuses and per-file error', async () => {
    mockDocuments(fetchMock, [
      makeDocument({ document_name: 'a.md', status: 'READY' }),
      makeDocument({ document_id: 'd2', document_name: 'b.pdf', status: 'PROCESSING' }),
      makeDocument({ document_id: 'd3', document_name: 'c.txt', status: 'FAILED', error: 'No extractable text' }),
    ]);

    render(<App />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('link', { name: /^Documents$/ }));

    expect(await screen.findByText('a.md')).toBeInTheDocument();
    expect(screen.getByText('Ready')).toBeInTheDocument();
    expect(screen.getByText('Processing')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByText('No extractable text')).toBeInTheDocument();
  });

  it('shows the empty state when no documents exist', async () => {
    mockDocuments(fetchMock, []);
    render(<App />);

    const user = userEvent.setup();
    await user.click(screen.getByRole('link', { name: /^Documents$/ }));

    expect(await screen.findByText(/no sources/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload documents/i })).toBeInTheDocument();
  });

  it('shows a safe error and Retry when the list request fails', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: 'down' }, 500));
    render(<App />);

    const user = userEvent.setup();
    await user.click(screen.getByRole('link', { name: /^Documents$/ }));

    expect(await screen.findByText(/could not load/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('uploads multiple files and keeps valid files despite one failure', async () => {
    mockDocuments(fetchMock, []);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        results: [
          { filename: 'good.md', status: 'READY', document_id: 'd-ok' },
          { filename: 'bad.pdf', status: 'FAILED', document_id: 'd-bad', error: 'No extractable text' },
        ],
      }),
    );

    render(<App />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('link', { name: /^Documents$/ }));

    const input = screen.getByLabelText(/upload documents/i) as HTMLInputElement;
    const good = new File(['# ok'], 'good.md', { type: 'text/markdown' });
    const bad = new File([''], 'bad.pdf', { type: 'application/pdf' });
    await user.upload(input, [good, bad]);
    await user.click(screen.getByRole('button', { name: /upload/i }));

    expect(await screen.findByText('good.md')).toBeInTheDocument();
    expect(screen.getByText('bad.pdf')).toBeInTheDocument();
    expect(screen.getByText('No extractable text')).toBeInTheDocument();
  });

  it('renders duplicate status without claiming a new document', async () => {
    mockDocuments(fetchMock, [
      makeDocument({ document_id: 'd1', document_name: 'dup.md', status: 'DUPLICATE' }),
    ]);

    render(<App />);
    const user = userEvent.setup();
    await user.click(screen.getByRole('link', { name: /^Documents$/ }));

    expect(await screen.findByText('Duplicate')).toBeInTheDocument();
  });
});

describe('App — query, answer, and evidence', () => {
  let fetchMock: ReturnType<typeof installFetch>;

  beforeEach(() => {
    fetchMock = installFetch();
  });

  it('shows empty-index guidance when no documents are READY', async () => {
    mockDocuments(fetchMock, []);
    render(<App />);

    expect(await screen.findByText(/upload a document and wait until it is ready/i)).toBeInTheDocument();
  });

  it('disables Run query for an empty question', async () => {
    mockDocuments(fetchMock, [makeDocument()]);
    render(<App />);

    await waitFor(() => expect(screen.getByRole('button', { name: /run query/i })).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /run query/i })).toBeDisabled();
  });

  it('submits POST /api/query once with the trimmed question using a relative URL', async () => {
    mockDocuments(fetchMock, [makeDocument()]);
    mockQuery(fetchMock, makeQueryResponse());

    render(<App />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText(/question/i), '  How much notice?  ');
    await user.click(screen.getByRole('button', { name: /run query/i }));

    await waitFor(() =>
      expect(fetchMock.mock.calls.map((c) => String(c[0]))).toContain('/api/query'),
    );

    const queryCall = fetchMock.mock.calls.find((c) => String(c[0]) === '/api/query');
    expect(JSON.parse(String(queryCall?.[1]?.body))).toEqual({ question: 'How much notice?' });
    expect(String(queryCall?.[0]).startsWith('/api/')).toBe(true);
    expect(fetchMock.mock.calls.filter((c) => String(c[0]) === '/api/query')).toHaveLength(1);
  });

  it('renders a complete answer with confidence, completeness, and an openable citation', async () => {
    mockDocuments(fetchMock, [makeDocument()]);
    mockQuery(fetchMock, makeQueryResponse());

    render(<App />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText(/question/i), 'How much notice?');
    await user.click(screen.getByRole('button', { name: /run query/i }));

    expect(await screen.findByText('The handbook requires two weeks notice.')).toBeInTheDocument();
    expect(screen.getByText('Complete')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();

    // AC-8: the first citation is open by default; the toggle still works.
    const citationButton = screen.getByRole('button', { name: /policy/i });
    expect(citationButton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Employees must provide two weeks notice.')).toBeInTheDocument();
    expect(screen.getByText('0.92')).toBeInTheDocument();

    await user.click(citationButton);
    expect(citationButton).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Employees must provide two weeks notice.')).not.toBeInTheDocument();

    await user.click(citationButton);
    expect(screen.getByText('Employees must provide two weeks notice.')).toBeInTheDocument();
  });

  it('renders a partial answer with missing info and suggestions before evidence', async () => {
    mockDocuments(fetchMock, [makeDocument()]);
    mockQuery(
      fetchMock,
      makeQueryResponse({
        is_complete: false,
        confidence: 'LOW',
        answer: 'Carry-over is unclear.',
        missing_info: ['Vacation carry-over policy is unknown.'],
        enrichment_suggestions: [
          { action_type: 'UPLOAD_DOCUMENT', target: 'HR handbook', reason: 'May hold the policy.', suggested_query: null },
        ],
      }),
    );

    render(<App />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText(/question/i), 'vacation carry-over');
    await user.click(screen.getByRole('button', { name: /run query/i }));

    expect(await screen.findByText('Incomplete')).toBeInTheDocument();
    expect(screen.getByText(/vacation carry-over policy is unknown/i)).toBeInTheDocument();
    expect(screen.getByText('HR handbook')).toBeInTheDocument();
  });

  it('presents INSUFFICIENT_DATA without citations or a factual answer', async () => {
    mockDocuments(fetchMock, [makeDocument()]);
    mockQuery(
      fetchMock,
      makeQueryResponse({
        confidence: 'INSUFFICIENT_DATA',
        is_complete: false,
        answer: 'No relevant evidence was retrieved for this question.',
        citations: [],
        enrichment_suggestions: [
          { action_type: 'ASK_USER', target: 'User', reason: 'Clarify the question.', suggested_query: 'Which team is affected?' },
        ],
      }),
    );

    render(<App />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText(/question/i), 'who won the 1999 world cup?');
    await user.click(screen.getByRole('button', { name: /run query/i }));

    expect(await screen.findByText('INSUFFICIENT_DATA')).toBeInTheDocument();
    expect(screen.getByText(/no relevant evidence/i)).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /evidence/i })).not.toBeInTheDocument();
    expect(screen.getByText('Which team is affected?')).toBeInTheDocument();
  });

  it('shows a safe request error with Retry and New query', async () => {
    mockDocuments(fetchMock, [makeDocument()]);
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: 'boom' }, 500));

    render(<App />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText(/question/i), 'x');
    await user.click(screen.getByRole('button', { name: /run query/i }));

    expect(await screen.findByText(/request could not be completed/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /new query/i })).toBeInTheDocument();
  });

  it('New query clears the previous result without making a backend call', async () => {
    mockDocuments(fetchMock, [makeDocument()]);
    mockQuery(fetchMock, makeQueryResponse({ answer: 'stale answer' }));

    render(<App />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText(/question/i), 'x');
    await user.click(screen.getByRole('button', { name: /run query/i }));
    await screen.findByText('stale answer');

    const callsBefore = fetchMock.mock.calls.length;
    await user.click(screen.getByRole('button', { name: /new query/i }));

    expect(screen.queryByText('stale answer')).not.toBeInTheDocument();
    expect(fetchMock.mock.calls.length).toBe(callsBefore);
  });

  it('omits nullable page/section/suggested_query fields without artifacts', async () => {
    mockDocuments(fetchMock, [makeDocument()]);
    mockQuery(
      fetchMock,
      makeQueryResponse({
        citations: [
          {
            chunk_id: 'c1',
            document_id: 'doc-1',
            document_name: 'notes.md',
            page_start: null,
            page_end: null,
            section: null,
            excerpt: 'plain text excerpt',
            relevance_score: 0.5,
          },
        ],
      }),
    );

    render(<App />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText(/question/i), 'x');
    await user.click(screen.getByRole('button', { name: /run query/i }));

    await screen.findByText('The handbook requires two weeks notice.');
    expect(screen.queryByText(/page/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/section/i)).not.toBeInTheDocument();
    expect(screen.queryByText('null')).not.toBeInTheDocument();
    expect(screen.queryByText('undefined')).not.toBeInTheDocument();
  });
});
