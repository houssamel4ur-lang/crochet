# CozyLoops production security rollout checklist

**Observed on 2026-11-14:** read-only GitHub Actions request checks found **0 of 6 expected HTTP response security headers** on the homepage, admin page and tulip article. The existing HTML `<meta http-equiv="Content-Security-Policy">` is not a replacement for a genuine HTTP security header. These are missing hardening controls, **not proof of six exploitable vulnerabilities**.

The code repository cannot set HTTP response headers on GitHub Pages. These steps require the **owner of the Cloudflare zone**. Do not paste DNS credentials or API tokens into a public repository or chat.

## Cloudflare — a single response header transform rule

1. Ensure the domain's DNS record is **Proxied** through Cloudflare and HTTPS is working.
2. Cloudflare dashboard > choose `cozyloops.site` > **Rules > Overview > Create rule > Response Header Transform Rule**.
3. Name it `CozyLoops safe response headers`. Choose a filter matching host `cozyloops.site`; do not modify unrelated sites.
4. Set the headers below using **Set static** operations. Review any existing conflicting rules. Do not simultaneously deploy `security/cloudflare-headers-worker.mjs` and a redundant transform without confirming precedence.

| HTTP response header | Initial safe value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Stop MIME-type guessing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Reduce unintended referrer leakage |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Block unused browser permissions |
| `X-Frame-Options` | `DENY` | Block clickjacking frames |
| `Content-Security-Policy` | `base-uri 'none'; object-src 'none'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests` | Enforce these rules using an **HTTP** header, including frame-ancestors |
| `Strict-Transport-Security` | `max-age=86400` | Start with a 1-day HSTS rollout; raise only when HTTPS is verified for all necessary hosts |

This conservative CSP intentionally **does not** add a public `script-src` that could disable the five HB Agency placements. It is **not** a full XSS policy; admin keeps its separate stricter meta CSP for script restrictions. Harden the public script policy only after a compatibility test of the actual ad delivery and CMP.

5. Deploy and rerun **Live Production Release Checks** in GitHub Actions. Confirm the resulting `cozyloops-live-security-headers` JSON artifact has the intended values on all three pages.
6. Verify login, article links, image uploads, ad placements and consent UI still work. Check browsers for new CSP violations.
7. After at least a day of verified uninterrupted HTTPS, consider increasing HSTS to `max-age=31536000`. Do **not** add `includeSubDomains` or `preload` without checking every subdomain.

Official instructions: https://developers.cloudflare.com/rules/transform/response-header-modification/create-dashboard/
HSTS caveats: https://developers.cloudflare.com/ssl/edge-certificates/additional-options/http-strict-transport-security/

## Supabase — owner-only audit

The Supabase connection used in this chat currently lists **zero projects**. No live RLS policy, function grant, storage policy, or authentication setting has been changed.

1. Connect the correct Supabase account/project.
2. In the project's SQL Editor, run the **read-only** queries in `supabase/rls_audit_readonly.sql`.
3. Review **every** exposed public table's RLS, `USING`/`WITH CHECK` clauses, `anon`/`authenticated` grants, all public `SECURITY DEFINER` functions, and object storage policies.
4. Check that the article image storage bucket only allows authorized admin writes, and that draft/scheduled articles never become public early.
5. Run Supabase security and performance advisors and address actual findings only after reviewing their impact. Do not blindly apply an RLS migration or accidentally block your existing Super Admin.

## Third-party advertising and content

- Existing five HB Agency ad placements are intentionally preserved. Latest Lighthouse mobile homepage had 8,660 ms TBT in one run, much of it attributed to ad/CMP code. Ask HB Agency to review its scripts, consent timing, cookies and long tasks. Do not remove ads or change consent behavior without a coordinated test.
- The managed Cloudflare `robots.txt` currently adds `Content-Signal: search=yes,ai-train=no,use=reference`; Lighthouse reports it as an unknown directive. The repository's own robots.txt is valid, and Cloudflare reports no observed SEO impact from its new content signals. Avoid changing AI crawler preferences just to chase a score.
- Review the audit table in `.github/editorial-quality-audit.md`. **18 articles** need clarity about AI visuals and **15 contact-sheet crop articles** need higher-resolution original photos. Technical WebP conversion does not restore lost image detail; physical pattern tests are necessary before calling them tested.

## Final acceptance

- GitHub Actions: Quality Checks, Browser UI Smoke Tests, Live Production Release Checks, Published Image Availability Audit, and Public Supabase Security Checks pass
- HTTP header inventory now shows appropriate values for each page (not merely `0/6`)
- Super Admin auth, scheduled publishing, images, consent and five ad placements are working on mobile and desktop
- No broken links, no missing article assets; sitemap and canonical URLs are consistent
- Original crochet patterns and true project photography have been reviewed for accuracy

Never report `100% secure` based on a score or a finite test set.
