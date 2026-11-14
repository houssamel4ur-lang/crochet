# CozyLoops HTTP security headers — deployment instructions

## Why this is needed

The 14 November 2026 SecurityHeaders screenshot checked
`http://cozyloops.site/` and received HTTP 200, without an HTTPS redirect
or the 5 required HTTP **response headers**. This is an external configuration
problem: GitHub Pages does not let a repository author set custom response
headers. A `<meta http-equiv="Content-Security-Policy">` in a page cannot
supply `X-Frame-Options`, `X-Content-Type-Options`, `Permissions-Policy`,
`Referrer-Policy`, or `frame-ancestors` as HTTP response headers.

The files in this directory are **deployment-ready, not deployed**.
Merely committing them does not change live security headers.

## First: turn on GitHub Pages' automatic HTTPS enforcement

1. Open https://github.com/houssamel4ur-lang/crochet/settings/pages
2. Verify that the custom domain is `cozyloops.site`, DNS check passes and
   the HTTPS certificate is valid.
3. Turn on **Enforce HTTPS**. If it is disabled, fix the domain/DNS or
   certificate provisioning before going further.
4. Confirm `http://cozyloops.site/` redirects to `https://cozyloops.site/`
   and does **not** return a 200 HTML page over HTTP.

GitHub documentation:
https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https

## Second: send security headers from an actual edge provider

**Option A — Cloudflare response-header transform rules:**

With `cozyloops.site` added to Cloudflare, DNS proxied (orange cloud) and
SSL/TLS mode safely configured so the origin certificate is valid:

- Enable **Always Use HTTPS**.
- Create Response Header Transform Rules for:
  - `Content-Security-Policy`: `base-uri 'none'; object-src 'none'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests`
  - `X-Frame-Options`: `DENY`
  - `X-Content-Type-Options`: `nosniff`
  - `Referrer-Policy`: `strict-origin-when-cross-origin`
  - `Permissions-Policy`: `camera=(), microphone=(), geolocation=()`
  - `Strict-Transport-Security`: `max-age=31536000` **only after verifying HTTPS works**.
- Do not blindly enable HSTS `includeSubDomains` or `preload`: confirm every
  subdomain is HTTPS-only first.
- Prefer scoping the CSP and X-Frame-Options to HTML pages; other headers
  can be emitted for all resources.
- Do not change `Access-Control-Allow-Origin: *` solely on the basis of
  the GitHub Pages static-file warning. For public static assets, wildcard
  CORS does not by itself expose authenticated user data.

Cloudflare docs: https://developers.cloudflare.com/rules/transform/response-header-modification/

**Option B — Cloudflare Worker (provided here):**

Deploy `cloudflare-headers-worker.mjs` as a Worker with route
`cozyloops.site/*` only *after* the domain is proxied by Cloudflare and
the existing origin continues to serve content. The Worker redirects HTTP,
proxies the existing response, adds six server response headers on HTTPS,
and applies no-store/noindex to the admin HTML.

Worker source: `security/cloudflare-headers-worker.mjs`
Tests: `node --test tests/security-edge.test.cjs`

**Do not apply the Worker while the domain is on plain GitHub Pages.**
Adding this file to the GitHub repository is not a deployment.

## Verification (after edge setup)

```sh
curl -sSI http://cozyloops.site/
curl -sSI https://cozyloops.site/
curl -sSI https://cozyloops.site/admin/
curl -sSI https://cozyloops.site/posts/crochet-patterns-for-beginners-guide/
```

Expected: HTTP redirects (301/308), HTTPS returns the header values above,
admin noindex/no-store. Then run https://securityheaders.com/?q=https%3A%2F%2Fcozyloops.site

Check homepage, published articles, admin login, Supabase API interactions,
images, advertising and mobile browsers. These headers only mitigate certain
browser risks; they are **not** a complete vulnerability scan. Supabase RLS,
Storage, privilege grants and server-side business logic require a separate
database audit. Keep a route to roll back Cloudflare rules if advertising,
login or content is affected.
