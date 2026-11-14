/* Tests the optional Cloudflare edge worker without touching production. */
const assert = require('node:assert/strict');
const {test} = require('node:test');
const {pathToFileURL} = require('node:url');
const {resolve} = require('node:path');

const workerModule = import(pathToFileURL(resolve(__dirname, '../security/cloudflare-headers-worker.mjs')).href);
test('redirects plaintext HTTP to HTTPS without contacting the origin', async () => {
  const worker = (await workerModule).default;
  const original = global.fetch;
  global.fetch = () => {throw new Error('should not fetch on HTTP')};
  try {
    const r = await worker.fetch(new Request('http://cozyloops.site/posts/test/?x=1'));
    assert.equal(r.status,308);
    assert.equal(r.headers.get('location'),'https://cozyloops.site/posts/test/?x=1');
  } finally {global.fetch = original}
});

test('sets real response headers for HTML but preserves advertising and body', async () => {
  const worker = (await workerModule).default;
  const original = global.fetch;
  global.fetch = async () => new Response('<p>Ads still render from origin</p>', {
    status:200,
    headers:{'content-type':'text/html; charset=utf-8','x-original':'kept'},
  });
  try {
    const r = await worker.fetch(new Request('https://cozyloops.site/'));
    assert.equal(r.headers.get('x-frame-options'),'DENY');
    assert.equal(r.headers.get('x-content-type-options'),'nosniff');
    assert.equal(r.headers.get('referrer-policy'),'strict-origin-when-cross-origin');
    assert.equal(r.headers.get('strict-transport-security'),'max-age=86400');
    assert.match(r.headers.get('content-security-policy'),/frame-ancestors 'none'/);
    assert.match(r.headers.get('permissions-policy'),/microphone=\(\)/);
    assert.equal(r.headers.get('x-original'),'kept');
    assert.match(await r.text(),/Ads still render/);
  } finally {global.fetch = original}
});

test('keeps non-HTML content intact and protects admin', async () => {
  const worker=(await workerModule).default;
  const original=global.fetch;
  global.fetch=async()=>new Response('ok',{headers:{'content-type':'application/javascript'}});
  try {
    const s=await worker.fetch(new Request('https://cozyloops.site/scripts/site_navigation.js'));
    assert.equal(s.headers.get('content-security-policy'),null);
    assert.equal(s.headers.get('x-content-type-options'),'nosniff');
    const admin=await worker.fetch(new Request('https://cozyloops.site/admin/'));
    assert.equal(admin.headers.get('x-robots-tag'),'noindex, nofollow');
    assert.equal(admin.headers.get('cache-control'),'no-store');
  } finally {global.fetch=original}
});
