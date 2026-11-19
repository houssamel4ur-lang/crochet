/**
 * Real Chromium UI smoke tests for CozyLoops.
 * Mock public Supabase GET requests for repeatable, safe, no-login tests.
 * Run with local server on :8765 and installed Playwright/Chromium.
 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const editorialCatalog = JSON.parse(fs.readFileSync(path.join(__dirname, '../content/github_articles.json'), 'utf8'));
const featuredEditorial = editorialCatalog.find(item => item.slug === 'crochet-patterns-for-beginners-guide');
if (!featuredEditorial) throw new Error('Browser fixture editorial article not found');
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
  // The real local browser server must expose the freshly generated SVG asset.
  const panel = await fetch(base + '/assets/editorial-illustrations/crochet-tulip-bouquet-stems-guide-panel-02.svg');
  assert.equal(panel.status, 200, 'Crisp editorial materials panel must be served');
  assert.match(await panel.text(), /FOLLOW THE WRITTEN INSTRUCTIONS/);
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    for (const viewport of [{ width: 1365, height: 900 }, { width: 390, height: 844 }]) {
      const page = await browser.newPage({ viewport, reducedMotion: 'reduce' });
      page.on('pageerror', error => failures.push(viewport.width + 'px: ' + error.message));
      await page.route('https://yqmrunstyhrhnvxoyrap.supabase.co/rest/v1/**', async route => {
        const url = route.request().url();
        let body = [];
        if (url.includes('/articles?')) body = [null, {slug:'bad slug',title:'Invalid Slug'}, {slug:'invalid-title',title:{unsafe:true}}, post];
        if (url.includes('/site_settings?')) body = [{ site_name: 'CozyLoops' }];
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body), headers: {'access-control-allow-origin': '*'} });
      });
      await page.route('**/content/github_articles.json', route => route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([featuredEditorial])
      }));
      await page.route('https://images.unsplash.com/**', route => route.abort());
      await page.goto(base + '/', { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => document.querySelectorAll('#postGrid .card').length === 2, {timeout:12000});
      assert.equal(await page.locator('#postGrid .card').count(), 2, 'GitHub editorial and mock Admin post, without retired starter posts');
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
      assert.equal(await page.locator('#postGrid .card', {hasText:'Crochet Patterns for Beginners'}).count(),1,'GitHub article is present in latest posts');
      const globalSearch = page.locator('.nav-search-trigger');
      assert.equal(await globalSearch.isVisible(), true, 'header search icon visible');
      await globalSearch.click();
      await page.waitForURL('**/#search-articles');
      await page.waitForFunction(() => document.activeElement?.id === 'search', {timeout:5000});
      assert.equal(await page.locator('#search').isVisible(), true, 'icon opens the article search');
      await page.locator('#search').fill('no-match-example');
      assert.match(await page.locator('#postGrid').innerText(), /No published articles found/);
      await page.locator('#search').fill('test crochet');
      assert.equal(await page.locator('#postGrid .card').count(), 1);
      assert.equal(await page.locator('.nav-menu-toggle').count(),0,'no hamburger icon');
      assert.equal(await page.locator('#site-drawer').count(),0,'no side drawer');
      const mainLinks=page.locator('header .top-links a');
      assert.deepEqual(await mainLinks.allTextContents(),['Home','Articles','Categories','About','Contact']);
      for (const link of await mainLinks.all()) assert.equal(await link.isVisible(),true,'all navigation links visible');
      assert.equal(await page.locator('header').evaluate(el => getComputedStyle(el).position),'relative','header scrolls away rather than sticking to the screen');
      if (viewport.width <= 760) {
        const rects=await mainLinks.evaluateAll(els=>els.map(el=>({top:el.getBoundingClientRect().top,right:el.getBoundingClientRect().right})));
        assert.ok(rects.every(r=>Math.abs(r.top-rects[0].top)<2),'all five mobile navigation links occupy one line');
        assert.ok(rects.every(r=>r.right <= viewport.width + 1),'all navigation links fit within the mobile viewport');
      }
      await page.locator('header .top-links a[href="/about/"]').click();
      await page.waitForURL('**/about/');
      assert.match(await page.locator('main h1').innerText(), /About CozyLoops/);
      await page.goto(base + '/#post/' + post.slug);
      await page.locator('main article h1').waitFor({ timeout: 12000 });
      assert.equal(await page.locator('main article h1').innerText(), post.title);
      assert.equal(await page.locator('main article h2').first().innerText(), 'Test Pattern');
      await page.goto(base + '/#privacy');
      await page.waitForURL('**/privacy-policy/');
      assert.match(await page.locator('main h1').innerText(), /Privacy Policy/);
      await page.locator('#opt-no').click();
      assert.match(await page.locator('#opt-status').innerText(), /disabled/);
      assert.equal(await page.evaluate(() => localStorage.getItem('cozyloops_analytics_consent')), 'no');
      await page.close();
      console.log('OK public browser smoke:', viewport.width + 'px');
    }
    // Check each standalone page at the requested 360/768/1024px breakpoints.
    for (const width of [360, 768, 1024]) {
      const legalPage = await browser.newPage({viewport:{width,height:800},reducedMotion:'reduce'});
      legalPage.on('pageerror', error => failures.push('legal '+width+'px: '+error.message));
      for (const slug of ['about','contact','privacy-policy','terms','disclosure','cookie-policy','sitemap']) {
        const response = await legalPage.goto(base+'/'+slug+'/', {waitUntil:'domcontentloaded'});
        if (slug === 'about') {
          assert.equal(await legalPage.locator('#cookie-consent').isVisible(), true, 'analytics consent banner displayed before choice');
          await legalPage.locator('#cookie-decline').click();
          assert.equal(await legalPage.evaluate(() => localStorage.getItem('cozyloops_analytics_consent')), 'no', 'analytics declined');
        }
        if (slug === 'contact') {
          assert.equal(await legalPage.locator('#contact-form').getAttribute('method'), 'POST', 'contact form is a real POST');
          assert.match(await legalPage.locator('#contact-form').getAttribute('action'), /^https:\/\/formsubmit\.co\//);
          for (const field of ['name','email','subject','message']) {
            assert.equal(await legalPage.locator('#contact-form [name="'+field+'"]').count(),1,field+' is sent to mail provider');
          }
        }
        if (slug === 'sitemap') {
          assert.ok(await legalPage.locator('.sitemap-articles a').count() >= 53, 'human sitemap lists published posts');
        }
        assert.equal(response.status(), 200, slug+' has a real standalone page');
        assert.equal(await legalPage.locator('main h1').count(),1,slug+' has one main heading');
        const overflowing = await legalPage.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
        assert.equal(overflowing,false,slug+' has no horizontal overflow at '+width+'px');
        assert.equal(await legalPage.locator('footer a[href="/sitemap.xml"]').count(),1,'sitemap link in footer');
      }
      await legalPage.close();
      console.log('OK standalone pages without overflow:',width+'px');
    }
    // Guard article reading progress and Back to Top against regressions.
    for (const viewport of [{width:1365,height:900},{width:390,height:844}]) {
      const articlePage = await browser.newPage({viewport,reducedMotion:'reduce'});
      articlePage.on('pageerror', error => failures.push('static article '+viewport.width+'px: '+error.message));
      await articlePage.addInitScript(() => localStorage.setItem('cozyloops_analytics_consent','no'));
      // Serve the analytics script from the repo so reading controls do not depend on the live site.
      await articlePage.route('https://cozyloops.site/scripts/article_analytics.js', route =>
        route.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync('scripts/article_analytics.js', 'utf8') })
      );
      await articlePage.goto(base+'/posts/crochet-patterns-for-beginners-guide/',{waitUntil:'domcontentloaded'});
      assert.equal(await articlePage.locator('.nav-menu-toggle').count(),0,'static article has no hamburger');
      assert.equal(await articlePage.locator('#site-drawer').count(),0,'static article has no drawer');
      const staticLinks=articlePage.locator('header .top-links a');
      assert.equal(await staticLinks.count(),5,'all five destinations available on static article');
      for (const link of await staticLinks.all()) assert.equal(await link.isVisible(),true,'static navigation link visible');
      assert.equal(await articlePage.locator('header').evaluate(el=>getComputedStyle(el).position),'relative','article header is not sticky');
      const articleSearch = articlePage.locator('.nav-search-trigger');
      assert.equal(await articleSearch.isVisible(), true, 'static article search icon visible');
      assert.equal(await articleSearch.getAttribute('href'), 'https://cozyloops.site/#search-articles');
      await articlePage.locator('#reading-progress [style]').count();
      assert.equal(await articlePage.locator('#back-to-top').isVisible(),false);
      await articlePage.evaluate(() => scrollTo(0, Math.min(document.documentElement.scrollHeight - innerHeight, 900)));
      await articlePage.waitForFunction(() => document.getElementById('back-to-top')?.hidden === false,{timeout:5000});
      assert.ok(Number(await articlePage.locator('#reading-progress').getAttribute('aria-valuenow')) > 0);
      await articlePage.locator('#back-to-top').click();
      await articlePage.waitForFunction(() => scrollY < 10,{timeout:5000});
      await articlePage.emulateMedia({media:'print'});
      assert.equal(await articlePage.locator('#back-to-top').evaluate(el => getComputedStyle(el).display),'none');
      assert.equal(await articlePage.locator('#reading-progress').evaluate(el => getComputedStyle(el).display),'none');
      await articlePage.close();
      console.log('OK static reading controls:',viewport.width+'px');
    }
    // Regression: untrusted article image URLs must not become HTML attributes.
    const hostile = await browser.newPage();
    hostile.on('pageerror', error => failures.push('hostile article: ' + error.message));
    const injected = {...post,
      slug:'untrusted-image-safety',
      title:'Safety test',
      image_url:'https://example.invalid/photo.jpg" onerror="document.body.dataset.injected=1',
      content:'## Safe heading\\n\\n![Alt](https://example.invalid/photo.jpg" onload="document.body.dataset.injected=1)'
    };
    await hostile.route('https://yqmrunstyhrhnvxoyrap.supabase.co/rest/v1/**', async route => {
      const response=route.request().url().includes('/articles?')?[injected]:[];
      await route.fulfill({status:200,contentType:'application/json',
        headers:{'access-control-allow-origin':'*'},body:JSON.stringify(response)});
    });
    await hostile.goto(base+'/#post/'+injected.slug,{waitUntil:'domcontentloaded'});
    await hostile.locator('main article h1').waitFor({timeout:12000});
    assert.equal(await hostile.locator('main article img').first().getAttribute('onerror'),null);
    assert.equal(await hostile.locator('main article img').first().getAttribute('onload'),null);
    assert.equal(await hostile.evaluate(()=>document.body.dataset.injected),undefined);
    await hostile.close();
    console.log('OK unsafe image attribute injection is blocked');
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    page.on('pageerror', error => failures.push('admin: ' + error.message));
    await page.goto(base + '/admin/', { waitUntil: 'domcontentloaded' });
    assert.equal(await page.locator('meta[name="robots"]').getAttribute('content'), 'noindex,nofollow');
    await page.locator('#login-view').waitFor({ state: 'visible', timeout: 12000 });
    assert.equal(await page.locator('#app-view').isVisible(), false, 'admin is not exposed to signed-out browser');
    await page.close();
    console.log('OK admin logged-out UI');
    // Exercise consent withdrawal from a generated SEO article as well.
    const staticPost = await browser.newPage();
    staticPost.on('pageerror', error => failures.push('static article: ' + error.message));
    const fsForStatic = require('node:fs');
    await staticPost.route('https://cozyloops.site/scripts/article_analytics.js', route =>
      route.fulfill({
        status:200,contentType:'application/javascript',
        body:fsForStatic.readFileSync('scripts/article_analytics.js','utf8')
      })
    );
    await staticPost.goto(base + '/posts/crochet-patterns-for-beginners-guide/', { waitUntil: 'domcontentloaded' });
    await staticPost.locator('#article-privacy-opt-out').waitFor({timeout:12000});
    await staticPost.locator('#article-privacy-opt-out').click();
    assert.equal(await staticPost.evaluate(() => localStorage.getItem('cozyloops_analytics_consent')), 'no');
    assert.match(await staticPost.locator('#article-consent-status').innerText(), /disabled/);
    await staticPost.close();
    console.log('OK static article privacy opt-out');

    // Simulate an authenticated but unauthorized account without using real credentials.
    const denied = await browser.newPage();
    denied.on('pageerror', error => failures.push('denied admin: ' + error.message));
    await denied.route('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js', route => route.fulfill({
      status: 200, contentType: 'application/javascript',
      headers: { 'access-control-allow-origin': '*' },
      body: [
        'window.supabase = { createClient: function(){ return {',
        ' auth: {',
        '  getSession: async function(){ return {data:{session:{access_token:"denied-token",user:{id:"test-user",email:"test@example.invalid"}}},error:null}; },',
        '  signInWithPassword: async function(){ return {data:{session:{access_token:"denied-token",user:{id:"test-user",email:"test@example.invalid"}}},error:null}; },',
        '  signOut: async function(){ return {error:null}; }',
        ' },',
        ' rpc: async function(){ return {data:false,error:null}; },',
        ' from: function(){ return { insert: async function(){ return {error:{message:"denied"}}; } }; }',
        '};} };'
      ].join('\n')
    }));
    await denied.goto(base + '/admin/', { waitUntil: 'domcontentloaded' });
    await denied.locator('#login-view').waitFor({ state: 'visible', timeout: 12000 });
    await denied.locator('#login-email').fill('test@example.invalid');
    await denied.locator('#login-password').fill('not-the-real-password');
    await denied.locator('#login-btn').click();
    await denied.locator('#denied-view').waitFor({ state: 'visible', timeout: 12000 });
    assert.equal(await denied.locator('#app-view').isVisible(), false, 'denied user must not see the admin');
    assert.match(await denied.locator('#denied-view').innerText(), /does not have admin access/);
    await denied.locator('#denied-back').click();
    await denied.locator('#login-view').waitFor({ state: 'visible', timeout: 5000 });
    assert.equal(await denied.locator('#app-view').isVisible(), false);
    await denied.close();
    console.log('OK denied Admin sign-out and recovery (mocked auth)');
    // Exercise the owner admin with an in-memory test database.
    const owner = await browser.newPage({ viewport: { width: 1365, height: 900 } });
    owner.on('pageerror', error => failures.push('owner admin: ' + error.message));
    const mockSource = fs.readFileSync('tests/mock-admin-supabase.mjs', 'utf8');
    await owner.route('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js', route => route.fulfill({
      status: 200, contentType: 'application/javascript',
      headers: { 'access-control-allow-origin': '*' }, body: mockSource
    }));
    await owner.route('**/rest/v1/articles*', async route => {
      const rows = await owner.evaluate(() => window.__mockAdminRows || []);
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(rows), headers: { 'access-control-allow-origin': '*' } });
    });
    await owner.goto(base + '/admin/', { waitUntil: 'domcontentloaded' });
    await owner.locator('#app-view').waitFor({ state: 'visible', timeout: 12000 });
    assert.match(await owner.locator('#side-who').innerText(), /houssam\.el\.4ur@gmail\.com/);
    await owner.locator('#side-nav [data-tab="articles"]').click();
    await owner.locator('[data-afilter="all"]').waitFor({ timeout: 12000 });
    await owner.locator('[data-act="article-new"]').click();
    await owner.locator('#f-title').waitFor({ state: 'visible', timeout: 5000 });
    await owner.locator('#f-title').fill('Safe CRUD Test Crochet');
    await owner.locator('#f-excerpt').fill('A test draft created in memory only.');
    await owner.locator('#f-content').fill('## Steps\n\nChain 10 stitches.');
    await owner.locator('#f-save').click();
    await owner.locator('.row-card', { hasText: 'Safe CRUD Test Crochet' }).waitFor({ timeout: 5000 });
    assert.equal(await owner.evaluate(() => window.__mockAdminRows.length), 1, 'draft stored only in test memory');
    assert.equal(await owner.evaluate(() => window.__mockAdminRows[0].status), 'draft');
    // The publish checklist blocks a thin draft from going live.
    await owner.locator('.row-card', { hasText: 'Safe CRUD Test Crochet' }).locator('[data-act="article-edit"]').click();
    await owner.locator('#f-title').waitFor({ state: 'visible', timeout: 5000 });
    await owner.locator('#f-status').selectOption('published');
    await owner.locator('#f-save').click();
    await owner.locator('#f-error:not(.hidden)').waitFor({ timeout: 5000 });
    assert.match(await owner.locator('#f-error').innerText(), /Publish checklist/);
    assert.equal(await owner.evaluate(() => window.__mockAdminRows[0].status), 'draft', 'rejected publish leaves the draft unpublished');
    await owner.locator('#f-cancel').click();
    await owner.locator('.row-card', { hasText: 'Safe CRUD Test Crochet' }).locator('[data-act="article-edit"]').click();
    await owner.locator('#f-title').waitFor({ state: 'visible', timeout: 5000 });
    await owner.locator('#f-status').selectOption('published');
    await owner.locator('#f-title').fill('Safe CRUD Test Crochet Updated');
    await owner.locator('#f-excerpt').fill('A detailed in-memory tutorial explaining crochet materials, sample stitches, accurate sizing and finishing without touching the live Supabase database.');
    await owner.locator('#f-image').fill('https://cozyloops.site/assets/crochet-tulip-bouquet-stems-guide-01.webp');
    const editorialTestSteps = ('Crochet a small test swatch, count every row, keep even tension, check your finished size and sew ends neatly. ').repeat(32);
    await owner.locator('#f-content').fill('## Materials and Hook\n\n' + editorialTestSteps +
      '\n\n![Crochet yarn and materials](https://cozyloops.site/assets/crochet-tulip-bouquet-stems-guide-02.webp)' +
      '\n\n## Stitch Instructions\n\n' + editorialTestSteps +
      '\n\n![Crochet project steps](https://cozyloops.site/assets/crochet-tulip-bouquet-stems-guide-04.webp)' +
      '\n\n## Finishing\n\nSecure the ends and check the finished project.');
    await owner.locator('#f-save').click();
    await owner.waitForFunction(() => window.__mockAdminRows[0]?.status === 'published');
    assert.equal(await owner.evaluate(() => window.__mockAdminRows[0].title), 'Safe CRUD Test Crochet Updated');
    await owner.locator('.row-card', { hasText: 'Safe CRUD Test Crochet Updated' }).locator('[data-act="article-edit"]').click();
    await owner.locator('#f-title').waitFor({ state: 'visible', timeout: 5000 });
    await owner.locator('#f-delete').click();
    await owner.locator('#f-delete').click();
    await owner.waitForFunction(() => window.__mockAdminRows.length === 0);
    console.log('OK authenticated Admin CRUD (in-memory mock)');
    await owner.locator('#side-nav [data-tab="pins"]').click();
    await owner.locator('.row-card').first().waitFor({ timeout: 12000 });
    assert.equal(await owner.locator('.row-card').count(), 60, 'all 60 pins are listed');
    await owner.locator('#side-nav [data-tab="ads"]').click();
    await owner.locator('.row-card').first().waitFor({ timeout: 12000 });
    assert.equal(await owner.locator('.row-card').count(), 6, 'all 6 HB Agency ad slots are listed');
    assert.match(await owner.locator('#main').innerText(), /349628/);
    await owner.locator('#side-nav [data-tab="pages"]').click();
    await owner.locator('[data-lang="ar"]').click();
    assert.equal(await owner.evaluate(() => document.documentElement.dir), 'rtl', 'Arabic switches the admin to RTL');
    await owner.locator('[data-lang="en"]').click();
    assert.equal(await owner.evaluate(() => document.documentElement.dir), 'ltr', 'English switches the admin back to LTR');
    await owner.close();
    console.log('OK authenticated Admin pins, ads and Arabic RTL');
    assert.deepEqual(failures, [], 'no browser JavaScript errors');
    console.log('All Chromium smoke checks passed');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
