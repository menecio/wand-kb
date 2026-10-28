import { test, expect } from '@playwright/test';

/**
 * Production same-origin journey tests.
 *
 * These run against the FastAPI-served production build at
 * http://127.0.0.1:8000 (docker compose up), not the Vite dev server.
 */

const uniqueDoc = {
  name: `zephyr-note-${Date.now()}.txt`,
  mimeType: 'text/plain',
  buffer: Buffer.from(
    'Prototype Note\n\nThe Zephyr prototype costs 42 credits and is built in the Lisbon workshop.',
  ),
};

test.beforeEach(async ({ page }) => {
  await page.goto('/');
});

test('upload, query, and open a citation in the production build', async ({ page }) => {
  test.setTimeout(180_000);

  // Upload through the real UI.
  await page.getByRole('link', { name: 'Documents' }).click();
  await page.getByLabel('Upload documents').setInputFiles([uniqueDoc]);
  await page.locator('form button[type="submit"]').click();
  await expect(page.getByText(uniqueDoc.name)).toBeVisible();
  await expect(page.getByText('READY').first()).toBeVisible();

  // Ask a question whose answer is only in the uploaded document.
  await page.getByRole('link', { name: 'Ask & answers' }).click();
  await page.getByLabel('Question').fill('How much does the Zephyr prototype cost?');
  await page.getByRole('button', { name: 'Run query' }).click();

  // The answer must appear with evidence.
  await expect(page.getByRole('region', { name: 'Evidence' })).toBeVisible({
    timeout: 150_000,
  });
  await expect(page.getByText('42')).toBeVisible();

  // Open the citation and check the excerpt against the uploaded source.
  await page.getByRole('button', { name: /zephyr-note/i }).click();
  await expect(
    page.getByRole('region', { name: 'Evidence' }).locator('blockquote'),
  ).toContainText('The Zephyr prototype costs 42 credits');
});

test('irrelevant query renders a controlled insufficient-data state', async ({ page }) => {
  test.setTimeout(120_000);

  await page.getByLabel('Question').fill('What is the capital of the lost city of Atlantis?');
  await page.getByRole('button', { name: 'Run query' }).click();

  await expect(page.getByText('INSUFFICIENT_DATA').first()).toBeVisible({
    timeout: 60_000,
  });
});

test('browser refresh does not trigger ingestion or queries', async ({ page }) => {
  const apiCalls: string[] = [];
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (url.pathname.startsWith('/api/')) {
      apiCalls.push(`${request.method()} ${url.pathname}`);
    }
  });

  await page.reload();
  await expect(page.getByRole('link', { name: 'Ask & answers' })).toBeVisible();

  // Only the document list may be fetched on load.
  const writeCalls = apiCalls.filter((call) => call.startsWith('POST'));
  expect(writeCalls).toEqual([]);
  expect(apiCalls).toContain('GET /api/documents');
});
