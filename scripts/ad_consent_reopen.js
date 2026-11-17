/* Bridge to an already-installed publisher consent manager (CMP).
 * Never fabricate TCF/GPP strings, toggle consent, or alter HB Agency ads.
 * The APIs below only REQUEST that the provider open its own preferences UI.
 */
(() => {
  'use strict';
  const tcfButton = document.getElementById('ad-consent-settings');
  const usButton = document.getElementById('us-privacy-settings');
  const status = document.getElementById('ad-consent-status');
  if (!status) return;

  function notice(message) { status.textContent = message; }
  tcfButton?.addEventListener('click', () => {
    const api = window.__tcfapi;
    if (typeof api === 'function') {
      try {
        // InMobi Choice's documented "Reprompt CMP API" (IAB TCF v2).
        api('displayConsentUi', 2, () => {});
        notice('Asked the advertising provider to open its consent choices. If no window appears, the provider may not be ready or may not offer this screen in your region. No choice was changed here.');
        return;
      } catch { /* Try supported alternate CMP below. */ }
    }
    const fc = window.googlefc;
    if (fc && typeof fc.showRevocationMessage === 'function') {
      try {
        fc.showRevocationMessage();
        notice('Asked the advertising provider to display its consent preferences. No choice was changed here.');
        return;
      } catch { /* Fall through to truthful unavailable status. */ }
    }
    notice('Advertising consent settings are unavailable in this browser. Contact the site operator or use browser privacy controls. No ad cookie settings were changed.');
  });

  usButton?.addEventListener('click', () => {
    const api = window.__uspapi;
    if (typeof api === 'function') {
      try {
        // InMobi's documented U.S. privacy-screen API.
        api('displayUspUi', 1, () => {});
        notice('Asked the provider to open U.S. privacy options. If no window appears, this region or provider configuration may not support them. No choice was changed here.');
        return;
      } catch { /* Fall through. */ }
    }
    notice('U.S. advertising privacy controls are not available from the installed provider in this browser. You can contact the site operator. No choice was changed here.');
  });
})();
