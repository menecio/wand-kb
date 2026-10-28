import { beforeEach, describe, expect, it } from 'vitest';
import { act, render, screen } from '@testing-library/react';
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

function mockDocuments(
  fetchMock: ReturnType<typeof installFetch>,
  documents: DocumentSummaryFixture[],
) {
  fetchMock.mockResolvedValueOnce(jsonResponse({ documents }));
}

describe('App audit remediation — documents states', () => {
  let fetchMock: ReturnType<typeof installFetch>;

  beforeEach(() => {
    fetchMock = installFetch();
  });

  // AC-5: generic wait while the initial GET is pending; the definitive
  // empty message appears only after a successful empty GET response.
  it('shows a generic wait (not the empty state) while the document list is loading', async () => {
    let resolveList: ((response: Response) => void) | undefined;
    fetchMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveList = resolve;
        }),
    );
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('link', { name: /^Documents$/ }));

    expect(screen.getByText(/loading documents/i)).toBeInTheDocument();
    expect(screen.queryByText(/no sources/i)).not.toBeInTheDocument();

    await act(async () => {
      resolveList?.(jsonResponse({ documents: [] }));
    });

    expect(await screen.findByText(/no sources/i)).toBeInTheDocument();
  });

  // AC-6: upload notice reflects per-file outcomes, never a blanket success.
  it('summarizes per-file upload outcomes in the notice', async () => {
    mockDocuments(fetchMock, []);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        results: [
          { filename: 'good.md', status: 'READY', document_id: 'd-ok' },
          { filename: 'bad.pdf', status: 'FAILED', document_id: 'd-bad', error: 'No extractable text' },
          { filename: 'notes.docx', status: 'REJECTED', document_id: null, error: 'Unsupported file type' },
        ],
      }),
    );

    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('link', { name: /^Documents$/ }));

    const input = screen.getByLabelText(/upload documents/i) as HTMLInputElement;
    const good = new File(['# ok'], 'good.md', { type: 'text/markdown' });
    const bad = new File([''], 'bad.pdf', { type: 'application/pdf' });
    const rejected = new File(['x'], 'notes.docx', { type: 'application/msword' });
    await user.upload(input, [good, bad, rejected]);
    await user.click(screen.getByRole('button', { name: /upload documents/i }));

    const notice = await screen.findByRole('status');
    expect(notice.textContent).toMatch(/1 file ready/i);
    expect(notice.textContent).toMatch(/1 file failed: bad\.pdf/i);
    expect(notice.textContent).toMatch(/1 file rejected: notes\.docx/i);
    expect(notice.textContent).not.toMatch(/upload complete/i);
  });

  // AC-6: idempotent duplicates are not reported as new documents.
  it('reports duplicate uploads as already-uploaded without claiming a new document', async () => {
    mockDocuments(fetchMock, []);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        results: [{ filename: 'dup.md', status: 'DUPLICATE', document_id: 'd-1', error: null }],
      }),
    );

    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('link', { name: /^Documents$/ }));

    const input = screen.getByLabelText(/upload documents/i) as HTMLInputElement;
    await user.upload(input, new File(['# dup'], 'dup.md', { type: 'text/markdown' }));
    await user.click(screen.getByRole('button', { name: /upload documents/i }));

    const notice = await screen.findByRole('status');
    expect(notice.textContent).toMatch(/1 already uploaded: dup\.md/i);
    expect(notice.textContent).toMatch(/no new document/i);
  });

  // AC-7: uploaded rows reconcile with the list by document_id.
  it('reconciles an uploaded duplicate with the existing row instead of appending a second row', async () => {
    mockDocuments(fetchMock, [
      makeDocument({ document_id: 'd-1', document_name: 'dup.md', status: 'READY' }),
    ]);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        results: [
          { filename: 'dup.md', status: 'DUPLICATE', document_id: 'd-1', error: null },
          { filename: 'fresh.md', status: 'READY', document_id: 'd-2', error: null },
        ],
      }),
    );

    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('link', { name: /^Documents$/ }));

    const input = screen.getByLabelText(/upload documents/i) as HTMLInputElement;
    await user.upload(input, [
      new File(['# dup'], 'dup.md', { type: 'text/markdown' }),
      new File(['# fresh'], 'fresh.md', { type: 'text/markdown' }),
    ]);
    await user.click(screen.getByRole('button', { name: /upload documents/i }));

    expect(await screen.findByText('fresh.md')).toBeInTheDocument();
    expect(screen.getAllByText('dup.md')).toHaveLength(1);
    expect(screen.getByText('Duplicate')).toBeInTheDocument();
  });

  // AC-9: statuses pair readable text with an aria-hidden icon.
  it('renders an aria-hidden icon next to every status label', async () => {
    mockDocuments(fetchMock, [
      makeDocument({ document_id: 'd1', document_name: 'a.md', status: 'READY' }),
      makeDocument({ document_id: 'd2', document_name: 'b.md', status: 'PROCESSING' }),
      makeDocument({ document_id: 'd3', document_name: 'c.md', status: 'FAILED', error: 'No extractable text' }),
    ]);

    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('link', { name: /^Documents$/ }));

    for (const label of ['Ready', 'Processing', 'Failed']) {
      const badge = (await screen.findByText(label)).closest('.status-badge');
      expect(badge).not.toBeNull();
      expect(badge?.querySelector('svg[aria-hidden="true"]')).not.toBeNull();
      expect(badge?.textContent).toContain(label);
    }
  });
});

describe('App audit remediation — query, answer, and evidence', () => {
  let fetchMock: ReturnType<typeof installFetch>;

  beforeEach(() => {
    fetchMock = installFetch();
  });

  // AC-4: empty-index state links to Documents and the link works.
  it('empty-index guidance navigates to Documents', async () => {
    mockDocuments(fetchMock, []);
    const user = userEvent.setup();
    render(<App />);

    expect(
      await screen.findByText(/upload a document and wait until it is ready/i),
    ).toBeInTheDocument();
    await user.click(screen.getByRole('link', { name: /go to documents/i }));

    expect(
      await screen.findByRole('button', { name: /upload documents/i }),
    ).toBeInTheDocument();
  });

  // AC-10: pending query shows text + spinner, blocks editing and resubmission.
  it('blocks question editing and shows text plus spinner while the query is pending', async () => {
    mockDocuments(fetchMock, [makeDocument()]);
    let resolveQuery: ((response: Response) => void) | undefined;
    fetchMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveQuery = resolve;
        }),
    );

    const user = userEvent.setup();
    render(<App />);
    await user.type(await screen.findByLabelText(/question/i), 'How much notice?');
    await user.click(screen.getByRole('button', { name: /run query/i }));

    const textarea = screen.getByLabelText(/question/i) as HTMLTextAreaElement;
    expect(textarea).toBeDisabled();
    expect(screen.getByRole('button', { name: /running/i })).toBeDisabled();

    const wait = screen.getByText(/searching and generating your answer/i);
    expect(wait).toBeInTheDocument();
    expect(wait.closest('[role="status"]')?.querySelector('svg[aria-hidden="true"]')).not.toBeNull();

    await act(async () => {
      resolveQuery?.(jsonResponse(makeQueryResponse()));
    });

    expect(await screen.findByText('The handbook requires two weeks notice.')).toBeInTheDocument();
    expect(screen.getByLabelText(/question/i)).toBeEnabled();
  });

  // AC-8: evidence heading shows the source count, the first citation opens
  // by default, C1/C2 labels are present, and toggles expose aria-expanded.
  it('evidence shows source count, C1 open by default, and C2 toggles with aria-expanded', async () => {
    mockDocuments(fetchMock, [makeDocument()]);
    mockQuery(
      fetchMock,
      makeQueryResponse({
        citations: [
          {
            chunk_id: 'chunk-1',
            document_id: 'doc-1',
            document_name: 'policy.md',
            page_start: 2,
            page_end: 2,
            section: null,
            excerpt: 'First excerpt text.',
            relevance_score: 0.9,
          },
          {
            chunk_id: 'chunk-2',
            document_id: 'doc-1',
            document_name: 'policy.md',
            page_start: 4,
            page_end: 5,
            section: null,
            excerpt: 'Second excerpt text.',
            relevance_score: 0.8,
          },
        ],
      }),
    );

    const user = userEvent.setup();
    render(<App />);
    await user.type(await screen.findByLabelText(/question/i), 'How much notice?');
    await user.click(screen.getByRole('button', { name: /run query/i }));

    const heading = await screen.findByRole('heading', { name: /evidence/i });
    expect(heading.textContent).toMatch(/2 sources/);

    const first = screen.getByRole('button', { name: /c1 .*policy\.md/i });
    const second = screen.getByRole('button', { name: /c2 .*policy\.md/i });
    expect(first).toHaveAttribute('aria-expanded', 'true');
    expect(second).toHaveAttribute('aria-expanded', 'false');

    expect(screen.getByText('First excerpt text.')).toBeInTheDocument();
    expect(screen.queryByText('Second excerpt text.')).not.toBeInTheDocument();

    await user.click(second);
    expect(second).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Second excerpt text.')).toBeInTheDocument();
  });
});

function mockQuery(fetchMock: ReturnType<typeof installFetch>, response: QueryResponseFixture) {
  fetchMock.mockResolvedValueOnce(jsonResponse(response));
}
