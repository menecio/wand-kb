import type { DocumentStatus } from '../types';

const LABELS: Record<DocumentStatus, string> = {
  PROCESSING: 'Processing',
  READY: 'Ready',
  FAILED: 'Failed',
  REJECTED: 'Rejected',
  DUPLICATE: 'Duplicate',
};

export default function StatusBadge({ status }: { status: DocumentStatus }) {
  return <span className={`status status--${status.toLowerCase()}`}>{LABELS[status]}</span>;
}
