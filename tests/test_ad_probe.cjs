const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const script = fs.readFileSync('/tmp/cb/article_analytics.js', 'utf8');

function setup(providers = {}) {
  const handlers = {};
  const timers = [];
  const el = (id) => ({
    id, hidden: true, textContent: '',
    addEventListener: (type, fn) => { handlers[id + '-' + type] = fn; },
    appendChild: () => {},
  });
  const elements = {
    'privacy-choice': el('privacy-choice'),
    'privacy-accept': el('privacy-accept'),
    'privacy-decline': el('privacy-decline'),
    'privacy-ad-settings': el('privacy-ad-settings'),
    'article-ad-consent-status': el('article-ad-consent-status'),
    'article-consent-status': el('article-consent-status'),
  };
  const store = {};
  const sandbox = {
    location: { pathname: '/posts/test-article/' },
    document: {
      getElementById: (id) => elements[id] || null,
      querySelector: (sel) => sel === 'footer' ? { appendChild: () => {} } : null,
      createElement: () => ({ type: '', textContent: '', style: {}, addEventListener: () => {} }),
    },
    localStorage: {
      getItem: (k) => (k in store ? store[k] : null),
      setItem: (k, v) => { store[k] = String(v); },
      removeItem: (k) => { delete store[k]; },
    },
    sessionStorage: { getItem: () => null, setItem: () => {} },
    navigator: { doNotTrack: '0' },
    crypto: { randomUUID: () => 'test-uuid' },
    matchMedia: () => ({ matches: false }),
    addEventListener: () => {},
    requestAnimationFrame: () => {},
    fetch: async () => { throw new Error('no network in test'); },
  };
  sandbox.window = {
    ...providers,
    setTimeout: (fn) => { timers.push(fn); return timers.length; },
  };
  sandbox.window.window = sandbox.window;
  vm.runInNewContext(script, sandbox);
  return { handlers, elements, timers, store, runTimers: () => { while (timers.length) timers.shift()(); } };
}

const UNAVAILABLE = 'not available';

// 1. No __tcfapi at all: probe exhausts, status is honest, click changes nothing.
{
  const s = setup();
  s.runTimers();
  assert.match(s.elements['article-ad-consent-status'].textContent, /not available/);
  s.handlers['privacy-ad-settings-click']();
  assert.match(s.elements['article-ad-consent-status'].textContent, /not available/);
  assert.equal(s.store['cozyloops_analytics_consent'], undefined, 'ad click must not write analytics consent');
  console.log('PASS 1: absent CMP -> honest unavailable, no consent written');
}

// 2. Working CMP: ping says loaded, click requests the real UI once.
{
  const calls = [];
  let pingCb = null;
  const s = setup({ __tcfapi: (cmd, v, cb) => { calls.push([cmd, v]); if (cmd === 'ping') pingCb = cb; } });
  s.runTimers(); // probe finds __tcfapi, calls ping
  assert.deepEqual(calls, [['ping', 2]]);
  pingCb({ cmpLoaded: true, gdprApplies: true, cmpStatus: 'loaded' });
  assert.match(s.elements['article-ad-consent-status'].textContent, /available from the advertising provider/);
  s.handlers['privacy-ad-settings-click']();
  assert.deepEqual(calls, [['ping', 2], ['displayConsentUi', 2]]);
  assert.match(s.elements['article-ad-consent-status'].textContent, /No advertising choice was changed/);
  console.log('PASS 2: loaded CMP -> ping then displayConsentUi on click only');
}

// 3. CMP present but not loaded: click does NOT call displayConsentUi.
{
  const calls = [];
  let pingCb = null;
  const s = setup({ __tcfapi: (cmd, v, cb) => { calls.push([cmd, v]); if (cmd === 'ping') pingCb = cb; } });
  s.runTimers();
  pingCb({ cmpLoaded: false, cmpStatus: 'error' });
  assert.match(s.elements['article-ad-consent-status'].textContent, /not available/);
  s.handlers['privacy-ad-settings-click']();
  assert.deepEqual(calls, [['ping', 2]], 'displayConsentUi must not be called when ping says not loaded');
  console.log('PASS 3: unloaded CMP -> click blocked, no displayConsentUi call');
}

// 4. No UI is auto-triggered on load, no fake signals, no cookie writes.
{
  const calls = [];
  const s = setup({ __tcfapi: (cmd, v, cb) => { calls.push(cmd); if (cmd === 'ping') cb({ cmpLoaded: true }); } });
  assert.deepEqual(calls, ['ping'], 'only ping on load, never displayConsentUi');
  assert.doesNotMatch(script, /__gpp\s*=|document\.cookie\s*=/);
  console.log('PASS 4: load only pings; no fake TCF/GPP, no cookie writes');
}
console.log('ALL AD-PROBE TESTS PASSED');
