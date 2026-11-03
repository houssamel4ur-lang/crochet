#!/usr/bin/env python3
"""Static acceptance checks for CozyLoops (no third-party dependencies)."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_BASE = "https://houssamel4ur-lang.github.io/crochet/"

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
        cls.admin = (ROOT / "admin/index.html").read_text(encoding="utf-8")
        cls.manifest = json.loads((ROOT / "posts/manifest.json").read_text(encoding="utf-8"))
        cls.sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")

    def test_home_has_metadata(self):
        scan = Scan()
        scan.feed(self.home)
        self.assertEqual(scan.main_count, 1)
        self.assertEqual(scan.canonicals, [PUBLIC_BASE])
        self.assertEqual(len(scan.descriptions), 1)
        self.assertGreater(len(scan.descriptions[0]), 35)
        self.assertEqual(len(scan.titles), 1)
        self.assertIn("CozyLoops", scan.titles[0])

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
        self.assertIn('class="mobile-menu"', self.home)
        self.assertIn(':focus-visible', self.home)
        self.assertIn('class="skip-link"', self.home)
        self.assertIn('srcset="${imageBase}photo-', self.home)
        self.assertIn('sizes="(max-width:800px)', self.home)
        self.assertIn('function route(preserveScroll=false)', self.home)
        self.assertIn('function readablePrimary(', self.home)
        self.assertTrue((ROOT / "favicon.svg").is_file())
        self.assertIn('rel="icon"', self.home)


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
