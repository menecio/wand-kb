// Types mirror the backend Pydantic schemas in backend/app/schemas/*.py
// (authoritative via /openapi.json). Kept in sync by hand for this phase.

export type DocumentStatus =
  | 'PROCESSING'
  | 'READY'
  | 'FAILED'
  | 'REJECTED'
  | 'DUPLICATE';

export interface DocumentSummary {
  document_id: string;
  document_name: string;
  content_sha256: string;
  status: DocumentStatus;
  error: string | null;
  created_at: string;
}

export interface DocumentList {
  documents: DocumentSummary[];
}

export interface DocumentDeleteResult {
  document_id: string;
  deleted: boolean;
}

export interface UploadResultItem {
  filename: string;
  status: DocumentStatus;
  document_id: string | null;
  error: string | null;
}

export interface DocumentUploadResult {
  results: UploadResultItem[];
}

export type Confidence = 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT_DATA';
export type ActionType = 'UPLOAD_DOCUMENT' | 'QUERY_EXTERNAL_SYSTEM' | 'ASK_USER';

export interface Citation {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_start: number | null;
  page_end: number | null;
  section: string | null;
  excerpt: string;
  relevance_score: number;
}

export interface EnrichmentSuggestion {
  action_type: ActionType;
  target: string;
  reason: string;
  suggested_query: string | null;
}

export interface QueryRequest {
  question: string;
}

export interface QueryResponse {
  response_id: string;
  answer: string;
  confidence: Confidence;
  is_complete: boolean;
  missing_info: string[];
  enrichment_suggestions: EnrichmentSuggestion[];
  citations: Citation[];
}
