/* Regression tests: provider UI must be requested only on user click.
 * No fake consent, no HB ad loading changes, no automatic CMP dialogs.
 */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const script = fs.readFileSync(path.join(__dirname,'../scripts/ad_consent_reopen.js'),'utf8');
function setup(providers={}) {
  const handlers = {};
  const state = { textContent:'' };
  const elements = {
    'ad-consent-settings': { addEventListener:(type,fn)=>{handlers['ad-'+type]=fn;} },
    'us-privacy-settings': { addEventListener:(type,fn)=>{handlers['us-'+type]=fn;} },
    'ad-consent-status': state,
  };
  const document = { getElementById:id=>elements[id]||null };
  const window = {...providers};
  vm.runInNewContext(script,{window,document});
  return {handlers,state,window};
}

test('never calls InMobi without an explicit user click',()=>{
  const calls=[];
  const s=setup({__tcfapi:(...args)=>calls.push(args)});
  assert.equal(calls.length,0);
  assert.equal(s.state.textContent,'');
  s.handlers['ad-click']();
  assert.equal(calls.length,1);
  assert.equal(calls[0][0],'displayConsentUi');
  assert.equal(calls[0][1],2);
  assert.match(s.state.textContent,/No choice was changed here/);
});

test('requests real U.S. provider privacy UI without fabricating choice',()=>{
  const calls=[];
  const s=setup({__uspapi:(...args)=>calls.push(args)});
  s.handlers['us-click']();
  assert.equal(calls.length,1);
  assert.equal(calls[0][0],'displayUspUi');
  assert.equal(calls[0][1],1);
  assert.match(s.state.textContent,/No choice was changed here/);
});

test('Google privacy and messaging is a safe fallback when InMobi absent',()=>{
  let calls=0;
  const s=setup({googlefc:{showRevocationMessage:()=>calls++}});
  s.handlers['ad-click']();
  assert.equal(calls,1);
  assert.match(s.state.textContent,/No choice was changed here/);
});

test('does not claim consent changed when CMP unavailable or throws',()=>{
  const first=setup();
  first.handlers['ad-click']();
  assert.match(first.state.textContent,/unavailable/);
  const second=setup({__tcfapi:()=>{throw Error('provider unavailable')}});
  second.handlers['ad-click']();
  assert.match(second.state.textContent,/unavailable/);
  second.handlers['us-click']();
  assert.match(second.state.textContent,/not available/);
});

test('never writes a fake TCF/GPP value or modifies local preferences',()=>{
  assert.doesNotMatch(script,/localStorage\.setItem|document\.cookie\s*=|__gpp\s*=|__tcfapi\s*=/);
});
