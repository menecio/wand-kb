import type {
  DocumentList,
  DocumentUploadResult,
  QueryRequest,
  QueryResponse,
} from '../types';

type ApiError = Error & { status?: number };

async function parse(response: Response) {
  if (!response.ok) {
    const error: ApiError = new Error('request_failed');
    error.status = response.status;
    throw error;
  }
  return response.json();
}

export async function listDocuments(): Promise<DocumentList> {
  const response = await fetch('/api/documents');
  return parse(response);
}

export async function uploadDocuments(files: File[]): Promise<DocumentUploadResult> {
  const form = new FormData();
  for (const file of files) {
    form.append('files', file);
  }
  const response = await fetch('/api/documents', { method: 'POST', body: form });
  return parse(response);
}

export async function query(body: QueryRequest): Promise<QueryResponse> {
  const response = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return parse(response);
}
