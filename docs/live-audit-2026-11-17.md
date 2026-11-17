# CozyLoops live performance, images and consent audit
**Measured:** 2026-11-17 UTC (GitHub Actions against https://cozyloops.site)

**Primary evidence**
- [Lighthouse run 43995732529](https://github.com/houssamel4ur-lang/crochet/actions/runs/43995732529) — four real Chromium reports, archived in the action's `cozyloops-lighthouse-report` artifact.
- [Published Image Availability Audit 43995732528](https://github.com/houssamel4ur-lang/crochet/actions/runs/43995732528).
- [Live Production Release Checks 43995732659](https://github.com/houssamel4ur-lang/crochet/actions/runs/43995732659).

## Measured Lighthouse results (not simulated)
| Page/device | Performance | Accessibility | Best Practices | SEO | LCP | TBT | CLS |
|---|---:|---:|---:|---:|---:|---:|---:|
| Home mobile | 95 | 95 | 75 | 92 | 2.1 s | 220 ms | 0 |
| Home desktop | 99 | 100 | 78 | 92 | 1.0 s | 0 ms | 0.003 |
| About mobile | 99 | 100 | 100 | 92 | 1.7 s | 0 ms | 0 |
| Beginner article mobile | 87 | 100 | 75 | 92 | 3.2 s | 240 ms | 0.048 |

Scores are one-run lab measurements and can vary with network, third-party ads, browser geolocation and load.

## What is fixed in code / what needs a provider

1. **Mobile touch targets:** Lighthouse identified 6 article title anchors under `article.card > div.card-body > h3 > a` with insufficient safe clickable space. Mobile-only CSS now gives these links block layout, ≥48px height and additional padding. Recheck after deployment before claiming the metric is resolved.
2. **Advertising CMP:** The live ad chain loaded `https://cmp.inmobi.com/tcfv2/cmp2.js?referer=hbagency.it`, and Chrome reported `TypeError: Cannot read properties of undefined (reading 'consents')` within that third-party script on Home and an article. InMobi Choice CMP appears in [Google's certified CMP list](https://support.google.com/adsense/answer/13554116) as CMP ID 10, **but certification of the vendor does not certify this site's configuration**. The HB Agency/InMobi owners must check domain mapping, TCF ping/loaded state, callback handling and real regional consent flows. Do not rewrite the third-party ad loader to mask the error.
3. **Visitor controls:** Cookie Policy now requests the installed TCF CMP's real `displayConsentUi` and U.S. `displayUspUi` only on a user click, using [InMobi's published callbacks](https://support.inmobi.com/choice/how-to-guide/callbacks/web-callbacks). It never invents consent or writes a TCF/GPP string. Actual availability remains jurisdiction/provider-dependent.
4. **Third-party image cookie:** Lighthouse found a `_cfuvid` cookie associated with `images.pexels.com` image requests. This is an external image CDN issue observed separately from the ads. Host exact licensed image assets locally only after verifying sources/rights and preserving the real image; avoid attributing this cookie to HB Agency.
5. **Cloudflare robots extension:** Lighthouse SEO flags `Content-Signal: search=yes,ai-train=no,use=reference` as an unknown `robots.txt` directive, explaining the common SEO score of 92. Cloudflare documents that its managed Content Signals can trigger such warnings and reports no observed crawler impact. Do **not** remove the owner's AI-crawler policy merely to raise a lab score; changing Cloudflare bot preferences requires owner intent.
6. **Back/forward cache:** Chrome's reason `NetworkExceedsBufferLimit` was marked *not actionable* in that test; do not promise a deterministic site-code fix.
7. **Response headers:** The live production audit found **0/6 security HTTP response headers** on five paths (Home, Admin, Contact, confirmation, and article). The optional repository Worker is **not** deployed as an edge policy; configuration in the Cloudflare zone remains necessary. See `security/PRODUCTION-SETUP.md`.

## Images / editorial standard
The live crawler checked **244 distinct referenced image URLs** across all **53 published posts**, finding **0 broken and 0 transient responses** and **53 unique hero image URLs**. This proves URL reachability in that run; it does **not** establish sharpness, photograph authenticity, crochet stitch accuracy, copyright clearance, or physically tested samples. The existing editorial audit still marks **18 concept-image articles** and **15 contact-sheet source articles** for human/real-source review.

## Unverified items
- Ad-provider's regional CMP state, TCF consent string validity, vendor list, and effects on real ad demand.
- Direct owner-side Supabase Auth/RLS/storage policies; current connector returns no projects, although public read-only API checks have passed in previous actions.
- Real post-activation email delivery from FormSubmit; owner reported activation, but no inbox receipt was independently verified.
- Original photographed project samples and physical stitch-count testing for all patterns.

## Site integrity
The original HB Agency loader, five ad placements, `ads.txt`, all 53 article slugs and original article bodies were intentionally not changed.
