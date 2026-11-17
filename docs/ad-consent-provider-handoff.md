# HB Agency / Google publisher CMP handoff — November 17, 2026

**Status:** The owner has live HB Agency advertising. A lightweight CozyLoops analytics choice is **not** an advertising CMP. Do not call the website GDPR/TCF compliant until actual regional ad consent is audited with the provider.

## Safeguards already applied
- Original `prebid_hb_40300_44798.js` script, placements, `ads.txt`, and advertising load order were not edited.
- The Cookie Policy separates optional Supabase analytics from third-party advertising technologies.
- The advertising-preferences button can reopen a **pre-existing** Google Privacy & messaging consent UI when `googlefc.showRevocationMessage` is available; it does not create a consent record.
- We have NOT generated fake `__tcfapi` or `__gpp` signals.

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
