# CozyLoops — Free Crochet Patterns & Tutorials

Live website: https://houssamel4ur-lang.github.io/crochet/  
Admin dashboard: https://houssamel4ur-lang.github.io/crochet/admin/

## How this website works
- GitHub Pages serves the public homepage, admin UI, and static article pages.
- Supabase provides published articles, private drafts, theme and social settings, image storage, and admin authentication.
- `scripts/build_seo.py` builds static article URLs and `sitemap.xml` from published articles.
- The `Update SEO article pages` GitHub Action checks for published article changes hourly. Newly published posts may appear on the homepage before their static SEO page is generated.
- No Supabase service-role or secret key belongs in this repository.

## Automated verification
| Workflow | What it checks |
| --- | --- |
| CozyLoops Quality Checks | Article metadata, generated pages, sitemap, JavaScript syntax |
| Browser UI Smoke Tests | Chromium desktop/mobile search, navigation, articles, privacy opt-out, denied-account recovery and mock Super Admin create/edit/publish/delete; does not use live credentials or alter production data |
| Public Supabase Security Checks | **Live read-only** anonymous access to published/draft posts, hidden social links, public theme, page-view rows, privileged RPCs |
| Lighthouse Performance Audit | Scheduled lab measurements of homepage and sample article; results vary between runs |
| Live Production Release Checks | Read-only checks of the deployed homepage, admin noindex, all published static articles, sitemap consistency, privacy controls, cover image alt/dimensions, share metadata and project-safe links |

Each workflow is available in the repository's **Actions** tab. A green run only verifies the listed checks; it does not guarantee the complete site or database is secure.

## Release checklist (owner verification required)
- [ ] Sign in as the designated Super Admin and verify create/edit/publish/draft/delete using a **temporary test article**; remove it after the test. (The browser workflow already exercises this sequence with an in-memory fake database; **production permissions remain unverified**.)
- [ ] Run the read-only SQL report `supabase/rls_audit_readonly.sql` in Supabase SQL Editor and inspect its output. It reports policy expressions, grants, roles and bucket configuration; it does not change them.
- [ ] In Supabase, review RLS and table/Storage policies: public may read only `published` articles and visible public settings; only the Super Admin can write content, settings and Storage; anonymous users cannot directly read `page_views`.
- [ ] Audit `SECURITY DEFINER` functions, execute grants, and ensure public view-count functions have anti-abuse safeguards. Current automated tests do not try unauthorized writes.
- [ ] Verify article image uploads (JPG/PNG/WebP/GIF, up to 5 MB) and that published images load on phones and desktop.
- [ ] Verify privacy consent and analytics opt-out on homepage and static articles. The Privacy page and each generated article have a local opt-out control that stops future optional analytics in that browser. Previously recorded counts are not deleted.
- [ ] Complete real operator contact information, Terms, and Privacy Policy before monetization, analytics extensions, or collecting visitor information.
- [ ] Add the exact URL-prefix property `https://houssamel4ur-lang.github.io/crochet/` to [Google Search Console](https://search.google.com/search-console), **verify ownership in the owner's Google account**, and submit `https://houssamel4ur-lang.github.io/crochet/sitemap.xml`. The static `robots.txt` within this project is *not* a host-root robots.txt.
- [ ] Use URL Inspection in Search Console after Google discovers pages; sitemap inclusion does **not** prove Google indexing.
- [ ] Re-run Lighthouse after deployment and sample real devices; verify navigation, accessibility, and Core Web Vitals. Lab scores fluctuate.
- [ ] Confirm production recovery: recent Supabase database backup/export, source repository access, and GitHub Pages settings.

## Safety notes
- Supabase public/publishable keys are intentionally visible in frontend code. Database protection depends on correctly enforced RLS and SQL grants, **not on hiding the publishable key**.
- `tests/public_api_security.py` makes read-only API requests (including read-only summary RPC) and does not create, change or delete records.
- Administrator write flows and database RLS policies require a human-authenticated release test; they have **not** been fully audited by automation.
