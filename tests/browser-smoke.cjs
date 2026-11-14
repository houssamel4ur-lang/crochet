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
      await page.locator('header .top-links a[href="#about"]').click();
      await page.waitForURL('**/#about');
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
    // Guard article reading progress and Back to Top against regressions.
    for (const viewport of [{width:1365,height:900},{width:390,height:844}]) {
      const articlePage = await browser.newPage({viewport,reducedMotion:'reduce'});
      articlePage.on('pageerror', error => failures.push('static article '+viewport.width+'px: '+error.message));
      await articlePage.addInitScript(() => localStorage.setItem('cozyloops_analytics_consent','no'));
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
    assert.equal(await page.locator('#dashboard').isVisible(), false, 'admin is not exposed to signed-out browser');
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
    await denied.route('https://esm.sh/@supabase/supabase-js@2', route => route.fulfill({
      status: 200, contentType: 'application/javascript',
      headers: {'access-control-allow-origin': '*'},
      body: [
        'let active=true;',
        'export function createClient(){return {',
        ' auth:{getUser:async()=>({data:{user:active?{id:"test-user",email:"test@example.invalid"}:null},error:null}),',
        ' signOut:async()=>{active=false;return {error:null};},',
        ' signInWithPassword:async()=>({error:null})},',
        ' rpc:async()=>({data:false,error:null})',
        '};}'
      ].join('\n')
    }));
    await denied.goto(base + '/admin/', { waitUntil: 'domcontentloaded' });
    await denied.locator('#denied-logout').waitFor({ state:'visible', timeout: 12000 });
    assert.equal(await denied.locator('#dashboard').isVisible(), false, 'denied user must not see dashboard');
    assert.match(await denied.locator('#message').innerText(), /does not have Super Admin access/);
    await denied.locator('#denied-logout').click();
    await denied.locator('#login').waitFor({state:'visible',timeout:5000});
    assert.equal(await denied.locator('#dashboard').isVisible(), false);
    await denied.close();
    console.log('OK denied Admin sign-out and recovery (mocked auth)');
    // Exercise an authorized editor with an in-memory test database.
    const fs = require('node:fs');
    const owner = await browser.newPage({viewport:{width:1365,height:900}});
    owner.on('pageerror', error => failures.push('owner admin: '+error.message));
    const mockSource=fs.readFileSync('tests/mock-admin-supabase.mjs','utf8');
    await owner.route('https://esm.sh/@supabase/supabase-js@2', route => route.fulfill({
      status:200,contentType:'application/javascript',
      headers:{'access-control-allow-origin':'*'},body:mockSource
    }));
    await owner.route('**/content/github_articles.json', route => route.fulfill({
      status:200,contentType:'application/json',
      body:JSON.stringify([featuredEditorial])
    }));
    await owner.goto(base+'/admin/',{waitUntil:'domcontentloaded'});
    await owner.locator('#dashboard').waitFor({state:'visible',timeout:12000});
    await owner.locator('.admin-nav button[data-panel="posts"][data-post-filter="all"]').click();
    const editorialRow=owner.locator('#posts-list .post-row',{hasText:'Crochet Patterns for Beginners'});
    await editorialRow.waitFor({timeout:5000});
    assert.equal(await owner.locator('#import-original-posts').count(),0,'deleted six-post importer is gone');
    assert.equal(await owner.locator('.editorial-import').count(),1,'editable GitHub editorial is listed');
    await owner.locator('#new-post').click();
    await owner.locator('#post-title').fill('Safe CRUD Test Crochet');
    await owner.locator('#post-excerpt').fill('A test draft created in memory only.');
    await owner.locator('#post-content').fill('## Steps\\n\\nChain 10 stitches.');
    await owner.locator('#post-status').selectOption('draft');
    await owner.locator('#save-post').click();
    await owner.locator('#posts-list .post-row').first().waitFor();
    assert.equal(await owner.evaluate(()=>window.__mockAdminRows.length),1,'draft stored only in test memory');
    assert.equal(await owner.evaluate(()=>window.__mockAdminRows[0].status),'draft');
    await owner.locator('#posts-list .post-row', {hasText:'Safe CRUD Test Crochet'}).locator('button.secondary').click();
    await owner.locator('#post-status').selectOption('published');
    await owner.locator('#post-title').fill('Safe CRUD Test Crochet Updated');
    await owner.locator('#post-excerpt').fill('A detailed in-memory tutorial explaining crochet materials, sample stitches, accurate sizing and finishing without touching the live Supabase database.');
    await owner.locator('#post-image').fill('https://cozyloops.site/assets/crochet-tulip-bouquet-stems-guide-01.webp');
    const editorialTestSteps = ('Crochet a small test swatch, count every row, keep even tension, check your finished size and sew ends neatly. ').repeat(32);
    await owner.locator('#post-content').fill('## Materials and Hook\n\n'+editorialTestSteps+
      '\n\n![Crochet yarn and materials](https://cozyloops.site/assets/crochet-tulip-bouquet-stems-guide-02.webp)'+
      '\n\n## Stitch Instructions\n\n'+editorialTestSteps+
      '\n\n![Crochet project steps](https://cozyloops.site/assets/crochet-tulip-bouquet-stems-guide-04.webp)'+
      '\n\n## Finishing\n\nSecure the ends and check the finished project.');
    await owner.locator('#save-post').click();
    await owner.waitForFunction(()=>window.__mockAdminRows[0]?.status==='published');
    assert.equal(await owner.evaluate(()=>window.__mockAdminRows[0].title),'Safe CRUD Test Crochet Updated');
    owner.once('dialog',dialog=>dialog.accept());
    await owner.locator('#posts-list .post-row .danger').first().click();
    await owner.waitForFunction(()=>window.__mockAdminRows.length===0);
    await owner.waitForFunction(() => document.querySelectorAll('#posts-list .post-row').length === 1, {timeout:5000});
    assert.equal(await owner.locator('#posts-list .post-row').count(),1,'GitHub editorial remains available for editing');
    await owner.locator('#posts-list .post-row .editorial-import').click();
    assert.equal(await owner.locator('#post-slug').inputValue(),'crochet-patterns-for-beginners-guide');
    assert.match(await owner.locator('#post-content').inputValue(),/What Is a Crochet Pattern/);
    owner.once('dialog',dialog=>dialog.accept('Finishing Tips'));
    await owner.locator('#post-add-article-section').click();
    assert.match(await owner.locator('#post-content').inputValue(),/## Finishing Tips/);
    owner.once('dialog',dialog=>dialog.accept());
    await owner.locator('#save-post').click();
    await owner.waitForFunction(()=>window.__mockAdminRows.some(p=>p.slug==='crochet-patterns-for-beginners-guide'));
    await owner.waitForFunction(() => document.querySelectorAll('#posts-list .editorial-import').length === 0 && !document.querySelector('#posts-list')?.classList.contains('hide'), {timeout:5000});
    assert.equal(await owner.locator('#posts-list .post-row .editorial-import').count(),0,'imported editorial is now a normal Admin post');
    await owner.locator('#posts-list .post-row',{hasText:'Crochet Patterns for Beginners'}).locator('button.secondary').click();
    await owner.locator('#post-title').fill('Crochet Patterns for Beginners (Edited)');
    await owner.locator('#save-post').click();
    await owner.waitForFunction(()=>window.__mockAdminRows.some(p=>p.title==='Crochet Patterns for Beginners (Edited)'));
    await owner.close();
    console.log('OK authenticated Admin CRUD, editorial import/edit, and Add Article Section (in-memory mock)');
    assert.deepEqual(failures, [], 'no browser JavaScript errors');
    console.log('All Chromium smoke checks passed');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
