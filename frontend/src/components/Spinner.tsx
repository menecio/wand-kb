import { LoaderCircle } from 'lucide-react';

/**
 * Supplementary spinner (spec §16): always paired with visible text so it is
 * never the only pending indicator; animation stops under reduced motion.
 */
export default function Spinner() {
  return <LoaderCircle size={16} aria-hidden="true" className="spinner" />;
}
