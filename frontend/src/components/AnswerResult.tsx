import type { QueryResponse } from '../types';
import CitationList from './CitationList';
import EnrichmentSuggestions from './EnrichmentSuggestions';

export default function AnswerResult({ result }: { result: QueryResponse }) {
  return (
    <article>
      <header>
        <span>{result.confidence}</span>
        <span>{result.is_complete ? 'Complete' : 'Incomplete'}</span>
      </header>

      <p>{result.answer}</p>

      {result.missing_info.length > 0 && (
        <section aria-label="Missing information">
          <h2>Missing information</h2>
          <ul>
            {result.missing_info.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
        </section>
      )}

      <EnrichmentSuggestions suggestions={result.enrichment_suggestions} />
      <CitationList citations={result.citations} />
    </article>
  );
}
