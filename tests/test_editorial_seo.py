"""Regression checks for the CozyLoops editorial standard across every GitHub article."""
import json
from pathlib import Path
import re
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from scripts.build_seo import (
    ROOT, IMAGE, normalize_article_content, concise_editorial_illustrations,
    render_page, seo_description, table_of_contents,
)

class EditorialSeoQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.posts = json.loads((ROOT / "content" / "github_articles.json").read_text(encoding="utf-8"))

    def test_all_editorials_have_distinct_search_snippets_and_valid_slugs(self):
        self.assertGreaterEqual(len(self.posts), 26)
        slugs, titles, descriptions = set(), set(), set()
        for post in self.posts:
            with self.subTest(slug=post.get("slug")):
                slug = post["slug"]
                self.assertRegex(slug, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                self.assertNotIn(slug, slugs)
                slugs.add(slug)
                title = post["title"].strip()
                self.assertGreaterEqual(len(title), 24)
                self.assertNotIn(title.casefold(), titles)
                titles.add(title.casefold())
                description = seo_description(post)
                self.assertGreaterEqual(len(description), 70)
                self.assertLessEqual(len(description), 160)
                self.assertNotIn(description.casefold(), descriptions)
                descriptions.add(description.casefold())
                self.assertTrue(post.get("image_url", "").startswith("https://"))
                self.assertGreaterEqual(len(post.get("image_alt", "").strip()), 12)
                body = post.get("content", "")
                self.assertGreaterEqual(len(re.findall(r"^##\s+.+$", body, re.M)), 3)
                embedded = list(IMAGE.finditer(body))
                self.assertGreaterEqual(len(embedded), 2)
                self.assertTrue(all(match.group(1).strip() for match in embedded))

    def test_long_tulip_navigation_is_collapsed_and_skips_faq_questions(self):
        post = next(post for post in self.posts if post["slug"] == "crochet-tulip-bouquet-stems-guide")
        body, note = normalize_article_content(post["content"])
        self.assertTrue(note.startswith("**Editorial note:**"))
        self.assertNotIn("**Editorial note:**", body)
        nav = table_of_contents(body)
        self.assertTrue(nav.startswith('<details class="article-toc">'))
        self.assertIn("Frequently Asked Questions", nav)
        self.assertNotIn("Do I need floral wire?", nav)
        self.assertLess(len(re.findall(r"<li>", nav)), 16)
        rendered = render_page(post, "body{color:#29342d}", self.posts)
        self.assertIn('class="article-hero concept-hero"', rendered)
        self.assertIn('class="article-disclosure"', rendered)
        self.assertIn('rel="canonical"', rendered)
        self.assertIn('name="twitter:description"', rendered)
        self.assertLess(rendered.index('<details class="article-toc">'), rendered.index("Quick Project Overview"))

    def test_generated_concept_posts_display_four_not_nine_large_images(self):
        concept_posts = [
            post for post in self.posts
            if "**Editorial note:** This article features original instructions and AI-generated" in post.get("content", "")
        ]
        self.assertGreaterEqual(len(concept_posts), 15)
        for post in concept_posts:
            with self.subTest(slug=post["slug"]):
                cleaned, disclosure = normalize_article_content(post["content"])
                self.assertTrue(disclosure)
                compact = concise_editorial_illustrations(cleaned)
                self.assertEqual(len(IMAGE.findall(compact)), 3)
                self.assertIn("-02.webp", compact)
                self.assertIn("-04.webp", compact)
                self.assertIn("-09.webp", compact)
                page = render_page(post, "body{color:#29342d}", self.posts)
                self.assertEqual(page.count("<figure"), 4)
                self.assertEqual(page.count('class="article-cover"'), 1)
                self.assertIn('content="summary_large_image"', page)

    def test_homepage_article_fallback_matches_static_editorial_rules(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function editorialViewContent(source)", html)
        self.assertIn("display.body?articleTableOfContents(display.body)", html)
        self.assertIn("display.note?'<details class=\"article-disclosure\"", html)
        self.assertIn("dynamic-concept-cover", html)
        self.assertIn("filter(entry=>entry.level===2)", html)
        self.assertIn("['02','04','09'].includes(num)", html)

if __name__ == "__main__":
    unittest.main()
