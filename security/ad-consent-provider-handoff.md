# HB Agency / Google publisher CMP handoff — November 17, 2026

**Update 2026-11-18 (PR: Show advertising cookie consent on first load):** the first-load banner now covers both choices on the homepage and on article pages. Article pages gained the same "Manage advertising cookies" button the homepage already had, wired to the genuine `__tcfapi('displayConsentUi', 2, ...)` / Google `showRevocationMessage` fallback. Both banners now probe CMP readiness with a read-only `__tcfapi('ping', 2, ...)` call (no UI shown, no consent written) and say honestly when the provider screen is unavailable, instead of implying one click opens it. Nothing here auto-opens the CMP, generates a TCF/GPP signal, or changes an HB placement. The InMobi `consents` TypeError and the missing auto-notice are still provider-side: HB Agency / InMobi must still confirm the `cozyloops.site` mapping and fix the vendor script.

**Status:** The owner has live HB Agency advertising. A lightweight CozyLoops analytics choice is **not** an advertising CMP. Do not call the website GDPR/TCF compliant until actual regional ad consent is audited with the provider.

## Safeguards already applied
- Original `prebid_hb_40300_44798.js` script, placements, `ads.txt`, and advertising load order were not edited.
- The Cookie Policy separates optional Supabase analytics from third-party advertising technologies.
- The advertising-preferences buttons can request the pre-existing InMobi TCF/USP privacy UI, or Google Privacy & messaging as a fallback. They do not create a consent record.
- We have NOT generated fake `__tcfapi` or `__gpp` signals.

## New direct-production evidence (2026-11-17)
- Lighthouse loaded an **InMobi Choice CMP** script from `cmp.inmobi.com/tcfv2/cmp2.js?referer=hbagency.it` within the HB Agency advertising chain. The browser logged `TypeError: Cannot read properties of undefined (reading 'consents')` from this third-party CMP on both the homepage and a crochet article.
- **InMobi Choice CMP is Google-certified (TCF CMP ID 10)** on Google's current publisher CMP list, but we have *not* verified whether this site has a working, correctly mapped, compliant consent configuration. A loaded script alone is not proof that consent is collected, stored, transmitted, or honored.
- The Cookie Policy's provider-preferences buttons now call genuine `__tcfapi('displayConsentUi',2,...)` and `__uspapi('displayUspUi',1,...)` when supplied by the existing InMobi integration. They do not generate artificial TCF/GPP signals or modify original HB tags. The old `googlefc.showRevocationMessage` fallback remains when present.
- On standalone legal pages, the original HB ad loader is intentionally absent. The Cookie Policy therefore links to `/#ad-privacy` on the homepage, where a user may explicitly request the installed consent UI via the same safe provider APIs. No consent flow is auto-triggered on navigation.
- Ask HB Agency / InMobi to confirm that `cozyloops.site` (not just the `hbagency.it` referer used in the CMP URL) is a correctly configured publisher property, that the `ping` and regional notice work, that an actual valid TC string is available where required, and that the runtime `consents` exception is resolved in vendor code. Don't patch the third-party minified script locally.
- The Google-certified vendor listing and InMobi API details are documented here: https://support.google.com/adsense/answer/13554116 and https://support.inmobi.com/choice/how-to-guide/callbacks/web-callbacks.

## Required from ad provider / owner before claiming CMP readiness
1. Confirm which advertising platform is actually used by the HB Agency stack (GAM/AdX/Prebid/AdSense etc.).
2. Confirm which **Google-certified IAB TCF CMP** is used for EEA, UK and Switzerland, and whether it supports the ad partners present. Decide ownership of CMP registration, vendor configurations, and website domain setup.
3. Confirm US state privacy requirements and GPP opt-out handling, including appropriate "Do Not Sell or Share" flows.
4. Verify a real consent string via provider-accepted TCF/GPP interfaces and how HB Agency's original tags honor it. Never create a dummy signal or move the ad script without coordinating with the ad provider.
5. Audit third-party domains, cookie inventory, cookies prior to consent where prohibited, consent renewal, revocation behavior and the policy's accurately named providers/retention.
6. Test sessions geolocated in relevant regions with browser devtools and actual partner traffic; preserve existing earnings/ad placements during any changes.
7. Ensure the site's Privacy Policy accurately describes verified providers and legal rights.

## Authority
- Google publisher CMP rules: https://support.google.com/adsense/answer/13554116
- Google CMP implementation choices: https://support.google.com/adsense/answer/16918505
- Official Google Privacy & messaging JavaScript API: https://developers.google.com/funding-choices/fc-api-docs

**Blocker:** Without the ad provider's CMP account/configuration and the published website's region-specific ad request evidence, changing the HB tags is both risky to revenue and insufficient to prove compliance.
