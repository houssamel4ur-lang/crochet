/* Shared consent banner on standalone CozyLoops pages. Never equate this with ad-tech consent. */
(() => {
  'use strict';
  const banner = document.getElementById('cookie-consent');
  if (!banner) return;
  const footer = document.querySelector('footer nav') || document.querySelector('footer');
  const manage = document.createElement('button');
  manage.type = 'button'; manage.textContent = 'Cookie settings'; manage.className = 'secondary';
  manage.style.cssText = 'min-height:44px;margin:8px;border-radius:10px;padding:8px 12px';
  manage.addEventListener('click', () => { banner.hidden = false; });
  footer?.appendChild(manage);
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
  banner.hidden = Boolean(consent());
})();
