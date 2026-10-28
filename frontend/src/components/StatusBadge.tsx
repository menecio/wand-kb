import { Ban, CircleAlert, CircleCheck, Copy, LoaderCircle } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { DocumentStatus } from '../types';

const LABELS: Record<DocumentStatus, string> = {
  PROCESSING: 'Processing',
  READY: 'Ready',
  FAILED: 'Failed',
  REJECTED: 'Rejected',
  DUPLICATE: 'Duplicate',
};

const ICONS: Record<DocumentStatus, LucideIcon> = {
  PROCESSING: LoaderCircle,
  READY: CircleCheck,
  FAILED: CircleAlert,
  REJECTED: Ban,
  DUPLICATE: Copy,
};

/** Text + complementary icon (§8, §17): state never depends on color alone. */
export default function StatusBadge({ status }: { status: DocumentStatus }) {
  const Icon = ICONS[status];
  return (
    <span className={`status-badge status-badge--${status.toLowerCase()}`}>
      <Icon
        size={16}
        aria-hidden="true"
        className={status === 'PROCESSING' ? 'spinner' : undefined}
      />
      <span>{LABELS[status]}</span>
    </span>
  );
}
