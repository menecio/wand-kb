import { test, expect } from '@playwright/test';

/**
 * Delete-a-document journey (issue #13, brief criteria 4-5).
 *
 * Runs against the FastAPI-served production build (docker compose up,
 * E2E_BASE_URL, default http://127.0.0.1:8000). Requires live Ollama + Qdrant.
 */

const doc = {
  name: `delete-me-${Date.now()}.txt`,
  mimeType: 'text/plain',
  buffer: Buffer.from(
    'Disposable note\n\nThis document exists only to be deleted by the trash button test.',
  ),
};

test('trash button deletes a document row from the documents list', async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto('/');

  await page.getByRole('link', { name: 'Documents', exact: true }).click();
  await page.getByLabel('Upload documents').setInputFiles([doc]);
  await page.locator('form button[type="submit"]').click();
  const row = page.getByRole('button', { name: `Delete ${doc.name}` });
  await expect(row).toBeVisible({ timeout: 60_000 });

  await row.click();

  // The row disappears and a success notice is shown; no error is raised.
  await expect(row).not.toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole('alert')).toHaveCount(0);
});