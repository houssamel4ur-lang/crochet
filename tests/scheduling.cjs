// Scheduling controls for the static admin, all writes in memory.
// Run with the local site served on port 8765.
const { chromium } = require('playwright');
const fs = require('fs');
const assert = require('node:assert/strict');
const path = require('node:path');
const SUPABASE_JS = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js';
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage({ timezoneId: 'UTC', viewport: { width: 1365, height: 900 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const mock = fs.readFileSync(path.join(__dirname, 'mock-admin-supabase.mjs'), 'utf8');
    await page.route(SUPABASE_JS, r => r.fulfill({ status: 200, contentType: 'application/javascript', body: mock }));
    // Drafts are read with the session token through the REST endpoint.
    await page.route('**/rest/v1/articles*', async r => {
      const rows = await page.evaluate(() => window.__mockAdminRows || []);
      await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(rows), headers: { 'access-control-allow-origin': '*' } });
    });
    await page.goto('http://127.0.0.1:8765/admin/', { waitUntil: 'domcontentloaded' });
    await page.locator('#app-view').waitFor({ state: 'visible', timeout: 12000 });
    await page.locator('#side-nav [data-tab="articles"]').click();
    await page.locator('[data-afilter="scheduled"]').waitFor({ timeout: 12000 });

    const target = await page.evaluate(() => {
      const d = new Date(Date.now() + 3600000);
      return d.toISOString().slice(0, 16);
    });
    const later = await page.evaluate(() => {
      const d = new Date(Date.now() + 7200000);
      return d.toISOString().slice(0, 16);
    });
    const row = page.locator('.row-card', { hasText: 'Schedule regression article' });

    // Create a draft scheduled one hour from now.
    await page.locator('[data-act="article-new"]').click();
    await page.locator('#f-title').waitFor({ state: 'visible', timeout: 5000 });
    await page.locator('#f-title').fill('Schedule regression article');
    await page.locator('#f-excerpt').fill('A mock-only scheduled draft.');
    await page.locator('#f-content').fill('## Instructions\n\nChain ten.');
    await page.locator('#f-scheduled').fill(target);
    await page.locator('#f-save').click();
    await page.waitForFunction(() => window.__mockAdminRows.length === 1);
    await row.waitFor({ timeout: 5000 });
    assert.equal(await page.evaluate(() => window.__mockAdminRows[0].status), 'draft');
    assert.ok(await page.evaluate(() => window.__mockAdminRows[0].scheduled_at.endsWith('Z')), 'scheduled_at is stored as ISO UTC');

    // The scheduled filter shows only drafts with a scheduled time.
    await page.locator('[data-afilter="scheduled"]').click();
    assert.equal(await page.locator('.row-card').count(), 1, 'scheduled view lists the draft');

    // Reopening the editor shows the same scheduled minute (UTC roundtrip).
    await row.locator('[data-act="article-edit"]').click();
    await page.locator('#f-title').waitFor({ state: 'visible', timeout: 5000 });
    assert.equal(await page.locator('#f-scheduled').inputValue(), target, 'UTC roundtrip preserves the scheduled minute');

    // Reschedule to a later time.
    const oldSched = await page.evaluate(() => window.__mockAdminRows[0].scheduled_at);
    await page.locator('#f-scheduled').fill(later);
    await page.locator('#f-save').click();
    await page.waitForFunction(old => window.__mockAdminRows[0].scheduled_at !== old, oldSched);
    assert.equal(await page.evaluate(() => window.__mockAdminRows[0].scheduled_at.slice(0, 16)), later);

    // Clearing the scheduled time removes the draft from the scheduled view.
    await row.locator('[data-act="article-edit"]').click();
    await page.locator('#f-title').waitFor({ state: 'visible', timeout: 5000 });
    await page.locator('#f-scheduled').fill('');
    await page.locator('#f-save').click();
    await page.waitForFunction(() => window.__mockAdminRows[0].scheduled_at === null);
    assert.equal(await page.evaluate(() => window.__mockAdminRows[0].status), 'draft');
    await page.waitForFunction(() => document.querySelectorAll('.row-card').length === 0);
    assert.equal(await page.locator('.row-card').count(), 0, 'cancelled schedules leave the scheduled view');

    // The draft itself remains in the full list.
    await page.locator('[data-afilter="all"]').click();
    await page.waitForFunction(() => document.querySelectorAll('.row-card').length === 1);
    assert.equal(await page.locator('.row-card').count(), 1, 'draft remains in all articles');
    assert.equal(await page.locator('.row-card', { hasText: 'Schedule regression article' }).count(), 1);

    assert.deepEqual(errors, []);
    await page.close();
    console.log('Scheduling UI: draft saves, scheduled filter, UTC roundtrip, reschedule and cancel passed.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
