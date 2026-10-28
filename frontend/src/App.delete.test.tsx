import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import App from './App';
import { installFetch, jsonResponse, makeDocument, type DocumentSummaryFixture } from './test/fixtures';

/**
 * Delete-a-document contract (issue #13, brief criteria 4-6):
 * - every document row has an accessible trash button ("Delete <name>"),
 * - clicking it sends DELETE /api/documents/{id} and removes the row,
 * - a failed delete shows an error notice and keeps the row.
 */

async function openDocuments(documents: DocumentSummaryFixture[]) {
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole('link', { name: /^Documents$/ }));
  for (const doc of documents) {
    await screen.findByRole('button', { name: new RegExp(`delete ${doc.document_name}`, 'i') });
  }
  return user;
}

describe('App — delete a document', () => {
  let fetchMock: ReturnType<typeof installFetch>;

  beforeEach(() => {
    fetchMock = installFetch();
  });

  it('renders a labelled trash button for every document row', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        documents: [makeDocument(), makeDocument({ document_id: 'd2', document_name: 'b.pdf' })],
      }),
    );
    await openDocuments([
      makeDocument(),
      makeDocument({ document_id: 'd2', document_name: 'b.pdf' }),
    ]);

    expect(screen.getByRole('button', { name: /delete policy\.md/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /delete b\.pdf/i })).toBeInTheDocument();
  });

  it('clicking trash sends DELETE /api/documents/{id} and removes the row', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ documents: [makeDocument()] }));
    const user = await openDocuments([makeDocument()]);

    fetchMock.mockResolvedValueOnce(jsonResponse({ document_id: 'doc-1', deleted: true }));
    await user.click(screen.getByRole('button', { name: /delete policy\.md/i }));

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((c) => [String(c[0]), (c[1] as RequestInit | undefined)?.method]);
      expect(calls).toContainEqual(['/api/documents/doc-1', 'DELETE']);
    });

    // The row disappears without a reload; a success notice is shown.
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /delete policy\.md/i })).not.toBeInTheDocument(),
    );
    expect(await screen.findByText(/policy\.md deleted/i)).toBeInTheDocument();
  });

  it('shows an error notice and keeps the row when the delete fails', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ documents: [makeDocument()] }));
    const user = await openDocuments([makeDocument()]);

    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: 'Qdrant unreachable' }, 503));
    await user.click(screen.getByRole('button', { name: /delete policy\.md/i }));

    expect(await screen.findByRole('alert')).toBeInTheDocument();
    // The row stays; the user can retry.
    expect(screen.getByRole('button', { name: /delete policy\.md/i })).toBeInTheDocument();
    expect(screen.queryByText(/policy\.md deleted/i)).not.toBeInTheDocument();
  });
});
