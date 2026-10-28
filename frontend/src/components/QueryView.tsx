import { useState } from 'react';
import { query as runQuery } from '../lib/api';
import type { QueryResponse } from '../types';
import AnswerResult from './AnswerResult';

interface QueryViewProps {
  hasReady: boolean;
}

export default function QueryView({ hasReady }: QueryViewProps) {
  const [question, setQuestion] = useState('');
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState(false);

  if (!hasReady) {
    return (
      <section>
        <h1>Ask &amp; answers</h1>
        <p>Upload a document and wait until it is ready before asking a question.</p>
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

  return (
    <section>
      <h1>Ask &amp; answers</h1>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit();
        }}
      >
        <label htmlFor="question">Question</label>
        <textarea
          id="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
        />
        <button type="submit" disabled={!question.trim() || pending}>
          {pending ? 'Running…' : 'Run query'}
        </button>
      </form>

      {pending && (
        <p role="status">Searching and generating your answer.</p>
      )}

      {error && (
        <div role="alert">
          <p>The request could not be completed. Try again.</p>
          <button type="button" onClick={() => void handleSubmit()}>
            Retry
          </button>
          <button type="button" onClick={() => { setQuestion(''); setResult(null); setError(false); }}>
            New query
          </button>
        </div>
      )}

      {result && (
        <>
          <AnswerResult result={result} />
          <button type="button" onClick={() => { setQuestion(''); setResult(null); setError(false); }}>
            New query
          </button>
        </>
      )}
    </section>
  );
}
