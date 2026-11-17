/* Production-only Chromium checks against https://cozyloops.site.
 * Never submit contact form, authenticate, change CMS data, or access private endpoints.
 */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const base = 'https://cozyloops.site';
const routes = [
  ['/', 'Home'],
  ['/about', 'About CozyLoops'],
  ['/contact', 'Contact CozyLoops'],
  ['/privacy-policy', 'Privacy Policy'],
  ['/terms', 'Terms of Use'],
  ['/disclosure', 'Editorial & Affiliate Disclosure'],
  ['/cookie-policy', 'Cookie Policy'],
  ['/sitemap', 'Site Map'],
  ['/posts/pink-axolotl-crochet-amigurumi-guide/', 'Axolotl article'],
];
const sleep = ms => new Promise(resolve => setTimeout(resolve,ms));
(async () => {
  fs.mkdirSync('artifacts', {recursive:true});
  const browser = await chromium.launch({headless:true,args:['--no-sandbox']});
  try {
    for (const width of [390,1024]) {
      const page = await browser.newPage({viewport:{width,height:850},reducedMotion:'reduce'});
      for (const [route,label] of routes) {
        const url = base + route;
        let lastError;
        for (let attempt=0;attempt<9;attempt++) {
          try {
            const response = await page.goto(url,{waitUntil:'domcontentloaded',timeout:25000});
            assert.ok(response, url+' did not return a navigation response');
            assert.equal(response.status(),200,url+' HTTP status');
            const title = await page.title();
            assert.ok(!/Page Not Found/i.test(title),url+' must not display the custom 404');
            assert.equal(await page.locator('main h1').count(),1,url+' must have one h1');
            if(width===390) {
              const bannerSelector = route==='/' || route.startsWith('/posts/') ? '#privacy-choice' : '#cookie-consent';
              assert.equal(await page.locator(bannerSelector).isVisible(),true,
                'Fresh visitor must see optional analytics banner on '+route);
            }
            const overflow = await page.evaluate(()=>document.documentElement.scrollWidth > innerWidth+1);
            assert.equal(overflow,false,route+' no horizontal overflow at '+width+'px');
            assert.ok(await page.locator('footer').count(),route+' has a footer');
            if(route === '/') {
              assert.equal(await page.locator('#ad-privacy').count(),1,
                'homepage must expose advertising provider preference controls');
              assert.equal(await page.locator('#ad-consent-settings').count(),1);
              assert.equal(await page.locator('#us-privacy-settings').count(),1);
            }
            if(route === '/contact' || route === '/cookie-policy') {
              const expectedEmail = 'houssam.el.4ur@gmail.com';
              await page.waitForFunction(email => [...document.querySelectorAll('main a')]
                .some(a => a.textContent.trim() === email), expectedEmail, {timeout:12000});
              const visibleEmail = await page.locator('main a').allTextContents();
              assert.ok(visibleEmail.some(v => v.trim() === expectedEmail),
                url + ' must visibly display the exact current contact email');
              console.log('LIVE EMAIL VERIFIED ' + url + ' at ' + width + 'px: ' + expectedEmail);
            }
            if(route === '/about') {
              assert.match(await page.locator('main').innerText(),/Houssam El Ouardy/);
              assert.equal(await page.locator('#cookie-consent').count(),1);
            }
            if(route === '/terms') {
              const content = await page.locator('main').innerText();
              assert.match(content,/November 16, 2026/);
              assert.ok(!/should be finalized before public launch|before public launch/i.test(content));
              if(width===390) await page.screenshot({path:'artifacts/cozyloops-live-terms-390.png',fullPage:true});
            }
            if(route === '/contact') {
              assert.equal(await page.locator('#contact-form').getAttribute('method'),'POST');
              assert.equal(await page.locator('#contact-form').getAttribute('action'),'https://formsubmit.co/houssam.el.4ur@gmail.com');
              assert.equal(await page.locator('#contact-form [name="message"]').count(),1);
              assert.equal(await page.locator('#contact-form [name="_next"]').getAttribute('value'), base+'/contact/thanks/');
              const confirmation = await page.request.get(base+'/contact/thanks/');
              assert.equal(confirmation.status(), 200, 'contact confirmation page must exist');
              assert.match(await confirmation.text(), /not proof that the message was delivered/);
            }
            if(route === '/cookie-policy') {
              await page.locator('#ad-consent-settings').click();
              assert.match(await page.locator('#ad-consent-status').innerText(),
                /Asked the advertising provider|Advertising consent settings are unavailable/);
              assert.equal(await page.locator('#us-privacy-settings').count(), 1,
                'Cookie Policy includes U.S. privacy option');
              // Do not force a second click over a real provider dialog; the
              // separate no-network unit test covers its actual callback.
            }
            if(route === '/sitemap') {
              assert.ok(await page.locator('.sitemap-articles a').count()>=53,'Sitemap shows all published articles');
            }
            if(route.startsWith('/posts/')) {
              const author=await page.locator('.article .meta').innerText();
              assert.match(author,/By Houssam El Ouardy/);
              assert.match(author,/Published [A-Z][a-z]+ \d{1,2}, 2026/);
              assert.match(author,/Updated [A-Z][a-z]+ \d{1,2}, 2026/);
              assert.match(author,/\d+ min read/);
              assert.equal(await page.locator('.author-bio').count(),1);
            }
            console.log('LIVE BROWSER OK '+url+' at '+width+'px | HTTP '+response.status()+' | '+label);
            lastError=null;
            break;
          } catch(err) {
            lastError=err;
            if(attempt>=8) throw err;
            await sleep(6000);
          }
        }
        if(lastError) throw lastError;
      }
      if(width===390) {
        await page.goto(base+'/about/',{waitUntil:'domcontentloaded'});
        await page.evaluate(()=>localStorage.removeItem('cozyloops_analytics_consent'));
        await page.reload({waitUntil:'domcontentloaded'});
        assert.equal(await page.locator('#cookie-consent').isVisible(),true,'Cookie banner appears before consent');
        await page.locator('#cookie-decline').click();
        assert.equal(await page.evaluate(()=>localStorage.getItem('cozyloops_analytics_consent')),'no');
        await page.screenshot({path:'artifacts/cozyloops-live-about-390.png',fullPage:true});
        await page.goto(base+'/#disclosure',{waitUntil:'domcontentloaded'});
        await page.waitForURL('**/disclosure/',{timeout:12000});
        assert.match(await page.locator('h1').innerText(),/Disclosure/);
        console.log('LIVE BROWSER OK '+base+'/#disclosure redirected to /disclosure/');
      }
      await page.close();
    }
    console.log('LIVE BROWSER VERIFICATION SUCCESS: all nine routes at 390px and 1024px');
  } finally {await browser.close();}
})().catch(e=>{console.error(e.stack||String(e));process.exitCode=1;});
