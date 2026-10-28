import type { EnrichmentSuggestion } from '../types';

const ACTION_LABELS = {
  UPLOAD_DOCUMENT: 'Upload document',
  QUERY_EXTERNAL_SYSTEM: 'Query external system',
  ASK_USER: 'Ask user',
} as const;

export default function EnrichmentSuggestions({
  suggestions,
}: {
  suggestions: EnrichmentSuggestion[];
}) {
  if (suggestions.length === 0) return null;

  return (
    <section aria-label="Enrichment suggestions">
      <h2>Enrichment suggestions</h2>
      <ul>
        {suggestions.map((suggestion, index) => (
          <li key={`${suggestion.action_type}-${suggestion.target}-${index}`}>
            <strong>{ACTION_LABELS[suggestion.action_type]}</strong>
            <h3>{suggestion.target}</h3>
            <p>{suggestion.reason}</p>
            {suggestion.suggested_query && (
              <p>Suggested question: <span>{suggestion.suggested_query}</span></p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
