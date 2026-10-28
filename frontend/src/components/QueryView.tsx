import { useState } from 'react';
import { query as runQuery } from '../lib/api';
import type { QueryResponse } from '../types';
import AnswerResult from './AnswerResult';
import Button from './ui/Button';
import Textarea from './ui/Textarea';
import Spinner from './Spinner';

interface QueryViewProps {
  hasReady: boolean;
  onNavigateToDocuments: () => void;
}

export default function QueryView({ hasReady, onNavigateToDocuments }: QueryViewProps) {
  const [question, setQuestion] = useState('');
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState(false);

  if (!hasReady) {
    return (
      <section>
        <h1>Ask &amp; answers</h1>
        <p>Upload a document and wait until it is ready before asking a question.</p>
        <a
          href="#documents"
          onClick={(event) => {
            event.preventDefault();
            onNavigateToDocuments();
          }}
        >
          Go to Documents
        </a>
      </section>
    );
  }

  async function handleSubmit() {
    const trimmed = question.trim();
    if (!trimmed || pending) return;

    setPending(true);
    setError(false);
    setResult(null);

    try {
      setResult(await runQuery({ question: trimmed }));
    } catch {
      setError(true);
    } finally {
      setPending(false);
    }
  }

  function resetForNewQuery() {
    setQuestion('');
    setResult(null);
    setError(false);
  }

  return (
    <section>
      <h1>Ask &amp; answers</h1>

      <form
        className="panel query-form"
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit();
        }}
      >
        <label htmlFor="question">Question</label>
        <Textarea
          id="question"
          value={question}
          placeholder="Ask a question about your documents"
          disabled={pending}
          onChange={(event) => setQuestion(event.target.value)}
        />
        <Button type="submit" disabled={!question.trim() || pending}>
          {pending ? (
            <>
              <Spinner /> Running…
            </>
          ) : (
            'Run query'
          )}
        </Button>
      </form>

      {pending && (
        <p role="status" className="state">
          <Spinner /> Searching and generating your answer.
        </p>
      )}

      {error && (
        <div role="alert" className="error-state panel">
          <p>The request could not be completed. Try again.</p>
          <Button variant="outline" onClick={() => void handleSubmit()}>
            Retry
          </Button>
          <Button variant="ghost" onClick={resetForNewQuery}>
            New query
          </Button>
        </div>
      )}

      {result && (
        <div className="result-actions">
          <AnswerResult result={result} />
          <Button variant="ghost" onClick={resetForNewQuery}>
            New query
          </Button>
        </div>
      )}
    </section>
  );
}
