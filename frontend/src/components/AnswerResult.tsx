import type { QueryResponse } from '../types';
import CitationList from './CitationList';
import EnrichmentSuggestions from './EnrichmentSuggestions';

/**
 * Result composition (§12, §14): header, then answer → gaps → suggestions in
 * the main column and evidence alongside it above 900px, after it below.
 */
export default function AnswerResult({ result }: { result: QueryResponse }) {
  return (
    <article>
      <header className="answer-header">
        <span
          className={`meta completeness completeness--${result.is_complete ? 'complete' : 'incomplete'}`}
        >
          {result.is_complete ? 'Complete' : 'Incomplete'}
        </span>
        <span className="meta confidence">
          Confidence: <span>{result.confidence}</span>
        </span>
      </header>

      <div className="result-grid">
        <div className="result-main">
          <p className="answer-text">{result.answer}</p>

          {result.missing_info.length > 0 && (
            <section aria-label="Missing information" className="panel missing-info">
              <h2>Missing information</h2>
              <ul>
                {result.missing_info.map((gap) => (
                  <li key={gap}>{gap}</li>
                ))}
              </ul>
            </section>
          )}

          <EnrichmentSuggestions suggestions={result.enrichment_suggestions} />
        </div>

        <CitationList citations={result.citations} />
      </div>
    </article>
  );
}
