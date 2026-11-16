/* Shared consent banner on standalone CozyLoops pages. Never equate this with ad-tech consent. */
(() => {
  'use strict';
  const banner = document.getElementById('cookie-consent');
  if (!banner) return;
  const key = 'cozyloops_analytics_consent';
  const consent = () => { try { return localStorage.getItem(key) || ''; } catch { return ''; } };
  const status = document.getElementById('opt-status');
  function choose(value) {
    try {
      localStorage.setItem(key, value);
      if (value === 'no') localStorage.removeItem('cozyloops_visitor_day');
    } catch {}
    banner.hidden = true;
    if (status) status.textContent =
      value === 'yes' ? 'CozyLoops analytics are enabled in this browser.' :
      'CozyLoops analytics are disabled in this browser.';
  }
  banner.querySelector('#cookie-accept')?.addEventListener('click', () => choose('yes'));
  banner.querySelector('#cookie-decline')?.addEventListener('click', () => choose('no'));
  banner.hidden = Boolean(consent()) || navigator.doNotTrack === '1';
})();
