/**
 * Real Chromium UI smoke tests for CozyLoops.
 * Mock public Supabase GET requests for repeatable, safe, no-login tests.
 * Run with local server on :8765 and installed Playwright/Chromium.
 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const base = 'http://127.0.0.1:8765';
const post = {
  title: 'CozyLoops Test Crochet Article',
  slug: 'cozyloops-ui-smoke-test',
  category: 'Free Patterns',
  excerpt: 'A sample article for browser testing the published post experience.',
  content: '## Test Pattern\n\nMake 10 chain stitches.\n\n- Yarn\n- Hook',
  image_url: 'https://images.unsplash.com/photo-1606761568499-6d2451b23c66?w=320',
  created_at: '2026-11-03T10:00:00Z',
  status: 'published'
};
const failures = [];
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    for (const viewport of [{ width: 1365, height: 900 }, { width: 390, height: 844 }]) {
      const page = await browser.newPage({ viewport, reducedMotion: 'reduce' });
      page.on('pageerror', error => failures.push(viewport.width + 'px: ' + error.message));
      await page.route('https://yqmrunstyhrhnvxoyrap.supabase.co/rest/v1/**', async route => {
        const url = route.request().url();
        let body = [];
        if (url.includes('/articles?')) body = [post];
        if (url.includes('/site_settings?')) body = [{ site_name: 'CozyLoops' }];
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body), headers: {'access-control-allow-origin': '*'} });
      });
      await page.route('https://images.unsplash.com/**', route => route.abort());
      await page.goto(base + '/', { waitUntil: 'domcontentloaded' });
      await page.locator('#postGrid .card').first().waitFor({ timeout: 12000 });
      assert.equal(await page.locator('#postGrid .card').count(), 1, 'published mock post visible');
      assert.equal(await page.locator('main h1').count(), 1, 'home has one h1');
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
      if (overflow) {
        const offenders = await page.evaluate(() => [...document.querySelectorAll('body *')].map(el => {
          const box = el.getBoundingClientRect();
          return { tag: el.tagName, className: String(el.className).slice(0,80), right: Math.round(box.right), left: Math.round(box.left), width: Math.round(box.width) };
        }).filter(el => el.right > innerWidth + 2 || el.left < -2).slice(0,18));
        console.error('Horizontal overflow offenders:', JSON.stringify(offenders));
      }
      assert.equal(overflow, false, viewport.width + 'px: no horizontal page overflow');
      await page.locator('#search').fill('no-match-example');
      assert.match(await page.locator('#postGrid').innerText(), /No published articles found/);
      await page.locator('#search').fill('test crochet');
      assert.equal(await page.locator('#postGrid .card').count(), 1);
      if (viewport.width < 650) {
        assert.equal(await page.locator('.mobile-menu').isVisible(), true);
        await page.locator('.mobile-menu summary').click();
        assert.equal(await page.locator('.mobile-menu').evaluate(el => el.open), true);
        await page.locator('.mobile-links a[href="#about"]').click();
        await page.waitForURL('**/#about');
        await page.waitForFunction(() => document.querySelector('.mobile-menu')?.open === false, { timeout: 5000 });
      }
      await page.goto(base + '/#post/' + post.slug);
      await page.locator('main article h1').waitFor({ timeout: 12000 });
      assert.equal(await page.locator('main article h1').innerText(), post.title);
      assert.equal(await page.locator('main article h2').first().innerText(), 'Test Pattern');
      await page.goto(base + '/#privacy');
      await page.locator('main h1').waitFor();
      assert.match(await page.locator('main h1').innerText(), /Privacy Policy/);
      await page.locator('#privacy-opt-out').click();
      assert.match(await page.locator('#privacy-consent-status').innerText(), /disabled/);
      assert.equal(await page.evaluate(() => localStorage.getItem('cozyloops_analytics_consent')), 'no');
      await page.close();
      console.log('OK public browser smoke:', viewport.width + 'px');
    }
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    page.on('pageerror', error => failures.push('admin: ' + error.message));
    await page.goto(base + '/admin/', { waitUntil: 'domcontentloaded' });
    assert.equal(await page.locator('meta[name="robots"]').getAttribute('content'), 'noindex,nofollow');
    assert.equal(await page.locator('#dashboard').isVisible(), false, 'admin is not exposed to signed-out browser');
    await page.close();
    console.log('OK admin logged-out UI');
    assert.deepEqual(failures, [], 'no browser JavaScript errors');
    console.log('All Chromium smoke checks passed');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
