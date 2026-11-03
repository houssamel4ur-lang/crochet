#!/usr/bin/env python3
"""Read-only production release smoke tests for the deployed GitHub Pages site.

No secrets, no credentials and no Supabase database writes. Run only after the
matching GitHub Pages deployment is available, to avoid false failures during
deployment propagation.
"""
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, urljoin
from xml.etree import ElementTree as ET
import json
import time
import unittest

BASE = "https://houssamel4ur-lang.github.io/crochet/"
EXPECTED_HOST = "houssamel4ur-lang.github.io"

def fetch(path, attempts=3):
    url = BASE + path
    assert urlsplit(url).hostname == EXPECTED_HOST
    last = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": "CozyLoops-ReadOnly-ReleaseCheck/1.0"})
            with urlopen(request, timeout=25) as response:
                final_url = response.geturl()
                if urlsplit(final_url).hostname != EXPECTED_HOST:
                    raise AssertionError("Unexpected redirect: " + final_url)
                if response.status != 200:
                    raise AssertionError("Unexpected HTTP " + str(response.status))
                return response.read().decode("utf-8", errors="replace")
        except Exception as err:
            last = err
            if attempt < attempts - 1:
                time.sleep(3)
    raise AssertionError("Could not fetch " + url + ": " + str(last))

class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.canonical = []
        self.meta_robots = []
        self.descriptions = []
        self.social = {}
        self.images = []
        self.links = []
        self.skip_link = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1": self.h1 += 1
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical.append(a.get("href"))
        if tag == "meta" and a.get("name") == "robots":
            self.meta_robots.append(a.get("content"))
        if tag == "meta" and a.get("name") == "description":
            self.descriptions.append(a.get("content", ""))
        if tag == "meta" and a.get("property", "").startswith("og:"):
            self.social[a["property"]] = a.get("content", "")
        if tag == "img":
            self.images.append(a)
        if tag == "a":
            self.links.append(a.get("href", ""))
            if a.get("class") == "skip-link":
                self.skip_link = True

class LiveSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = fetch("")
        cls.admin = fetch("admin/")
        cls.manifest = json.loads(fetch("posts/manifest.json"))
        cls.sitemap_text = fetch("sitemap.xml")

    def test_public_home_is_accessible(self):
        self.assertIn("CozyLoops", self.home)
        self.assertIn('id="app"', self.home)
        self.assertIn('rel="canonical" href="' + BASE + '"', self.home)

    def test_admin_is_noindex(self):
        tags = Tags()
        tags.feed(self.admin)
        self.assertTrue(any("noindex" in item for item in tags.meta_robots))
        self.assertIn('id="login"', self.admin)

    def test_sitemap_matches_live_article_manifest(self):
        root = ET.fromstring(self.sitemap_text)
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        urls = [e.text for e in root.findall(f"{ns}url/{ns}loc")]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(set(urls), {BASE} | {BASE + "posts/" + slug + "/" for slug in self.manifest})

    def test_all_live_articles_are_crawlable(self):
        self.assertGreater(len(self.manifest), 0)
        for slug in self.manifest:
            with self.subTest(slug=slug):
                self.assertRegex(slug, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                html = fetch("posts/" + slug + "/")
                tags = Tags()
                tags.feed(html)
                self.assertEqual(tags.h1, 1)
                self.assertEqual(tags.canonical, [BASE + "posts/" + slug + "/"])
                self.assertIn('id="article-privacy-opt-out"', html)
                self.assertIn('scripts/article_analytics.js', html)
                self.assertIn('"@type": "BlogPosting"', html)
                self.assertEqual(len(tags.descriptions), 1)
                self.assertGreater(len(tags.descriptions[0]), 30)
                self.assertEqual(tags.social.get("og:url"), BASE + "posts/" + slug + "/")
                self.assertTrue(tags.social.get("og:title"))
                self.assertTrue(tags.skip_link, "Missing skip-to-content link")
                self.assertGreater(len(tags.images), 0, "Article needs at least a cover image")
                for image in tags.images:
                    self.assertTrue(image.get("alt"), "Missing image alt text")
                    self.assertTrue(image.get("width"), "Missing image width")
                    self.assertTrue(image.get("height"), "Missing image height")
                    self.assertEqual(urlsplit(image.get("src", "")).scheme, "https")
                for link in tags.links:
                    if not link or link.startswith(("#", "mailto:", "tel:")):
                        continue
                    absolute = urljoin(BASE + "posts/" + slug + "/", link)
                    split = urlsplit(absolute)
                    self.assertIn(split.scheme, ("https",), "Insecure article link: " + absolute)
                    if split.hostname == EXPECTED_HOST:
                        self.assertTrue(split.path.startswith("/crochet/"), "Link escapes project: " + absolute)


    def test_navigation_assets_and_internal_destinations(self):
        """Check that shared public static links resolve on the live site."""
        expected = ["favicon.svg", "admin/", "scripts/article_analytics.js",
                    "posts/manifest.json", "sitemap.xml"]
        for path in expected:
            with self.subTest(path=path):
                body = fetch(path)
                self.assertGreater(len(body), 0, path + " is unexpectedly empty")
        # Public navigation links from the built homepage should target the
        # app's real section IDs or supported hash routes.
        for link in ("#home", "#articles", "#categories", "#about", "#contact"):
            self.assertIn('href="' + link + '"', self.home)

    def test_custom_404_page_and_robots(self):
        html = fetch("404.html")
        self.assertIn("Page Not Found | CozyLoops", html)
        self.assertIn('<meta name="robots" content="noindex,follow">', html)
        self.assertIn('href="/crochet/"', html)
        robots = fetch("robots.txt")
        self.assertIn("Sitemap: " + BASE + "sitemap.xml", robots)

    def test_article_reading_controls_available(self):
        for slug in self.manifest:
            with self.subTest(slug=slug):
                html = fetch("posts/" + slug + "/")
                self.assertEqual(html.count('id="reading-progress"'), 1)
                self.assertEqual(html.count('id="back-to-top"'), 1)

    def test_analytics_script_available(self):
        script = fetch("scripts/article_analytics.js")
        self.assertIn('article-privacy-opt-out', script)
        self.assertIn('cozyloops_analytics_consent', script)

if __name__ == "__main__":
    unittest.main(verbosity=2)
