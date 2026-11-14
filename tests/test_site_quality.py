#!/usr/bin/env python3
"""Static acceptance checks for CozyLoops (no third-party dependencies)."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_BASE = "https://cozyloops.site/"

class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.titles = []
        self.in_title = False
        self.descriptions = []
        self.canonicals = []
        self.headings = []
        self.images = []
        self.main_count = 0
        self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.titles.append("")
            self.in_title = True
        if tag == "meta" and a.get("name") == "description":
            self.descriptions.append(a.get("content", ""))
        if tag == "link" and a.get("rel") == "canonical":
            self.canonicals.append(a.get("href", ""))
        if tag in ("h1", "h2", "h3"):
            self.headings.append(tag)
        if tag == "img":
            self.images.append(a)
        if tag == "main":
            self.main_count += 1
        if tag == "a":
            self.links.append(a.get("href", ""))
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
    def handle_data(self, text):
        if self.in_title:
            self.titles[-1] += text

class SiteQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.admin = ((ROOT / "admin/index.html").read_text(encoding="utf-8") + '\n'
                     + (ROOT / "admin/app.js").read_text(encoding="utf-8"))
        cls.manifest = json.loads((ROOT / "posts/manifest.json").read_text(encoding="utf-8"))
        cls.sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")

    def test_hb_agency_ad_script_preserves_original_loading_setup(self):
        """Keep the provider's original nonblocking script in home and future posts."""
        provider = 'https://d3u598arehftfk.cloudfront.net/prebid_hb_40300_44798.js'
        for name, content in [
            ('homepage', self.home),
            ('SEO article builder', (ROOT / 'scripts/build_seo.py').read_text(encoding='utf-8')),
        ]:
            with self.subTest(page=name):
                self.assertIn(f'<script defer fetchpriority="low" src="{provider}"></script>', content)
                self.assertNotIn(f'fetchpriority="high" src="{provider}"', content)
        for slug in self.manifest:
            content = (ROOT / 'posts' / slug / 'index.html').read_text(encoding='utf-8')
            self.assertIn(provider, content)

    def test_mobile_navigation_and_article_touch_targets(self):
        home = self.home
        self.assertIn('.top-links a{grid-column:auto;min-width:0;width:100%;min-height:44px;', home)
        self.assertIn('grid-template-columns:minmax(0,1fr) 44px', home)
        self.assertIn('.top-nav .nav-search-trigger{grid-area:search;justify-self:end;width:44px;height:44px}', home)
        self.assertIn('.article-share-button{min-height:44px;', home)
        self.assertIn('.article-print-button{min-height:44px;', home)
        builder = (ROOT / 'scripts/build_seo.py').read_text(encoding='utf-8')
        self.assertIn('.article-share-button{{min-height:44px;', builder)
        self.assertIn('.article-print-button{{min-height:44px;', builder)

    def test_home_has_metadata(self):
        scan = Scan()
        scan.feed(self.home)
        self.assertEqual(scan.main_count, 1)
        self.assertEqual(scan.canonicals, [PUBLIC_BASE])
        self.assertEqual(len(scan.descriptions), 1)
        self.assertGreater(len(scan.descriptions[0]), 35)
        self.assertEqual(len(scan.titles), 1)
        self.assertIn("CozyLoops", scan.titles[0])

    def test_dynamic_article_image_attribute_is_escaped(self):
        self.assertIn("esc(safeHttps(p.image)", self.home)
        self.assertNotIn('src="${p.image}"', self.home)

    def test_article_links_are_hydrated_after_each_render(self):
        # Sucuri previously treated JavaScript template fragments as real
        # href values and reported invented URLs as 404 pages.
        self.assertIn("const articleLinkAttribute='href';", self.home)
        self.assertNotIn('href="${postHref(', self.home)
        self.assertNotIn('href="${esc(postHref(', self.home)
        self.assertNotIn("href=\"\u0027+esc(postHref(", self.home)
        self.assertIn("function updateCardLinks()", self.home)
        self.assertRegex(self.home, r"(?s)function drawCards\(\).*?updateCardLinks\(\)")
        self.assertIn("  drawStarterGuides();\n  updateCardLinks();", self.home)
        self.assertIn("  updateCardLinks();\n}\nfunction categoryPage", self.home)
        self.assertIn("  updateCardLinks();\n}\nfunction renderArticleMarkdown", self.home)
        self.assertIn(" updateCardLinks();\n requestAnimationFrame(scheduleReadingProgress)", self.home)

    def test_admin_not_indexable(self):
        self.assertRegex(self.admin, r'<meta name="robots" content="noindex,nofollow">')
        self.assertIn("is_super_admin", self.admin)
        self.assertIn("sb_publishable_", self.admin)
        self.assertNotIn("sb_secret_", self.admin)

    def test_admin_editor_validates_real_uploads_and_heading_hierarchy(self):
        self.assertIn("file.slice(0,16).arrayBuffer()", self.admin)
        self.assertIn("actualType!==file.type", self.admin)
        self.assertIn("file.size>5*1024*1024", self.admin)
        self.assertIn("Math.min(3,Math.max(2,match[1].length))", self.admin)

    def test_new_editorial_uploads_reject_low_resolution_and_repeated_images(self):
        self.assertIn("const minHeight=kind==='cover'?540:400;", self.admin)
        self.assertIn("if(bitmap.width<minWidth||bitmap.height<minHeight)", self.admin)
        self.assertIn("if(ratio<0.5||ratio>2.5)", self.admin)
        self.assertIn("m[1].trim().length>=12", self.admin)
        self.assertIn("new Set(imageUrls).size!==imageUrls.length", self.admin)

    def test_owner_release_guidance_is_available_without_false_claims(self):
        self.assertIn("Owner launch verification", self.admin)
        self.assertIn("supabase/rls_audit_readonly.sql", self.admin)
        self.assertIn("search.google.com/search-console", self.admin)
        self.assertIn("Automated checks do not mark them completed.", self.admin)
        self.assertIn("Real Admin test:", self.admin)

    def test_admin_has_operational_seo_health_panel(self):
        self.assertIn('id="panel-settings"', self.admin)
        self.assertIn('id="check-seo-health"', self.admin)
        self.assertIn("posts/manifest.json", self.admin)
        self.assertIn("sitemap.xml", self.admin)
        self.assertIn("search.google.com/search-console", self.admin)
        self.assertIn("Sitemap and published SEO article list do not match.", self.admin)

    def test_all_generated_posts_have_good_metadata(self):
        self.assertEqual(len(self.manifest), len(set(self.manifest)))
        self.assertGreater(len(self.manifest), 0)
        for slug in self.manifest:
            with self.subTest(slug=slug):
                self.assertRegex(slug, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                path = ROOT / "posts" / slug / "index.html"
                self.assertTrue(path.is_file())
                content = path.read_text(encoding="utf-8")
                scan = Scan()
                scan.feed(content)
                self.assertEqual(scan.main_count, 1)
                self.assertEqual(scan.headings.count("h1"), 1)
                self.assertEqual(len(scan.titles), 1)
                self.assertEqual(len(scan.descriptions), 1)
                self.assertGreater(len(scan.descriptions[0]), 30)
                self.assertEqual(scan.canonicals, [PUBLIC_BASE + "posts/" + slug + "/"])
                self.assertIn('"@type": "BlogPosting"', content)
                self.assertIn('id="article-privacy-opt-out"', content)
                self.assertIn('id="article-consent-status"', content)
                self.assertIn('scripts/article_analytics.js', content)
                for image in scan.images:
                    self.assertTrue(image.get("alt"), "image is missing meaningful alt text")
                self.assertIn(PUBLIC_BASE + "posts/" + slug + "/", self.sitemap)

    def test_site_has_consent_and_accessibility(self):
        self.assertIn('id="privacy-choice"', self.home)
        self.assertIn("analyticsConsent()", self.home)
        self.assertIn('class="nav top-nav"', self.home)
        self.assertIn(':focus-visible', self.home)
        self.assertIn('class="skip-link"', self.home)
        about = re.search(r'(?s)<section class="section feature"[^>]*>.*?<img ([^>]+)>', self.home)
        self.assertIsNotNone(about, "About section needs a crochet photo")
        attrs = dict(re.findall(r'([A-Za-z0-9_-]+)="([^"]*)"', about.group(1)))
        self.assertGreaterEqual(len(attrs.get('alt', '').strip()), 20)
        if attrs.get('srcset'):
            self.assertTrue(attrs.get('sizes'), "Responsive About photo requires sizes")
        else:
            # An optimized local WebP may be served without responsive variants.
            self.assertTrue(attrs.get('src', '').startswith('/assets/'))
            self.assertTrue(attrs['src'].endswith('.webp'))
            self.assertTrue((ROOT / attrs['src'].lstrip('/')).is_file())
            self.assertGreaterEqual(int(attrs.get('width', 0)), 500)
            self.assertGreaterEqual(int(attrs.get('height', 0)), 400)
        self.assertIn('function route(preserveScroll=false)', self.home)
        self.assertIn('function readablePrimary(', self.home)
        self.assertTrue((ROOT / "favicon.svg").is_file())
        self.assertIn('rel="icon"', self.home)


    def test_custom_404_has_accessible_navigation_and_noindex(self):
        page = (ROOT / "404.html").read_text(encoding="utf-8")
        self.assertIn('<meta name="robots" content="noindex,follow">', page)
        self.assertIn('href="/"', page)
        self.assertIn("<h1>", page)
        self.assertIn("Page Not Found | CozyLoops", page)

    def test_static_article_scroll_controls(self):
        script = (ROOT / "scripts/article_analytics.js").read_text(encoding="utf-8")
        self.assertIn('getElementById("back-to-top")', script)
        self.assertIn("updateBackToTop();", script)
        self.assertIn("requestAnimationFrame(update)", script)
        for slug in self.manifest:
            page = (ROOT / "posts" / slug / "index.html").read_text(encoding="utf-8")
            self.assertEqual(page.count('id="reading-progress"'), 1)
            self.assertEqual(page.count('id="back-to-top"'), 1)

    def test_github_editorial_content_is_published_and_illustrated(self):
        articles = json.loads((ROOT / "content/github_articles.json").read_text(encoding="utf-8"))
        self.assertTrue(articles)
        self.assertIn("content/github_articles.json", self.home)
        for article in articles:
            self.assertEqual(article["status"], "published")
            self.assertRegex(article["slug"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertTrue(article["image_url"].startswith("https://"))
            self.assertGreaterEqual(article["content"].count("![") + 1, 3)
            self.assertIn("## Frequently Asked Questions", article["content"])

    def test_removed_seed_posts_never_reappear(self):
        retired = {"crochet-for-absolute-beginners", "how-to-read-crochet-patterns",
            "easy-crochet-scarf-guide", "amigurumi-basics", "choosing-crochet-yarn", "crochet-stitch-counting"}
        self.assertFalse((ROOT / "content/original_articles.json").exists())
        self.assertTrue(retired.isdisjoint(self.manifest))
        for slug in retired:
            self.assertFalse((ROOT / "posts" / slug / "index.html").exists())
        self.assertNotIn("Import 6 Original Posts", self.admin)
        self.assertIn("removedStarterSlugs", self.home)
        self.assertIn("REMOVED_STARTER_SLUGS", (ROOT / "scripts/build_seo.py").read_text(encoding="utf-8"))

    def test_restored_saved_design_and_top_navigation(self):
        self.assertNotIn("CozyLoops Theme B", self.home)
        self.assertIn("photos/4792079/pexels-photo-4792079.jpeg", self.home)
        self.assertIn('class="top-links"', self.home)
        self.assertNotIn('id="site-drawer"', self.home)
        self.assertIn("scripts/site_navigation.js", self.home)
        self.assertIn('const posts=[featuredEditorial];', self.home)
        self.assertIn('crochet-patterns-for-beginners-guide', self.home)
        self.assertTrue((ROOT / "scripts/site_navigation.js").is_file())

    def test_global_search_navigation_available(self):
        self.assertIn('class="nav-search-trigger"', self.home)
        self.assertIn('href="#search-articles"', self.home)
        self.assertIn("path==='search-articles'", self.home)
        self.assertIn("input.focus({preventScroll:true})", self.home)
        for slug in self.manifest:
            content = (ROOT / "posts" / slug / "index.html").read_text(encoding="utf-8")
            self.assertIn('class="nav-search-trigger"', content)
            self.assertIn(PUBLIC_BASE + "#search-articles", content)

    def test_sitemap_contains_only_valid_public_urls(self):
        from xml.etree import ElementTree as ET
        root = ET.fromstring(self.sitemap)
        namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        urls = [e.text for e in root.findall(f"{namespace}url/{namespace}loc")]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(set(urls), {PUBLIC_BASE} | {PUBLIC_BASE + "posts/" + slug + "/" for slug in self.manifest})
        self.assertNotIn("/admin/", self.sitemap)

if __name__ == "__main__":
    unittest.main(verbosity=2)
