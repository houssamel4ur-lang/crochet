"""Regression checks for the CozyLoops editorial standard across every GitHub article."""
import json
from pathlib import Path
import re
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from scripts.build_seo import (
    ROOT, IMAGE, normalize_article_content, concise_editorial_illustrations,
    render_page, seo_description, table_of_contents, has_physical_test_evidence,
    extract_faq, related_articles, resolve_author, render_author_page,
    AUTHORS, AUTHORS_BY_CATEGORY, KEEP_HOUSSAM_SLUGS, HOUSSAM_AUTHOR,
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
                # Keep the article's original WebP panels until a reviewed
                # high-resolution replacement is actually available.
                for number in ("02", "04", "09"):
                    self.assertIn(f"/assets/{post['slug']}-{number}.webp", page)
                    self.assertNotIn(f"-panel-{number}.webp", page)
                self.assertIn("AI-generated concept image — not a photograph of a physically made sample.", page)


    def test_no_fabricated_physical_pattern_testing(self):
        registry = json.loads((ROOT / "content" / "pattern_testing_records.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["verified_patterns"], {})
        self.assertFalse(has_physical_test_evidence({
            "slug": "crochet-dollhouse-bed-runner",
            "pattern_tested": True,
            "tested_photo_url": "https://cozyloops.site/assets/illustration.webp",
        }))
        sample = {
            "slug": "crochet-dollhouse-bed-runner",
            "title": "Dollhouse Bed Runner",
            "content": "**Pattern status:** Original, untested construction draft.\n\n## Materials\n\nUse cotton yarn.",
            "excerpt": "A miniature crochet bed runner."
        }
        page = render_page(sample, "body{color:#29342d}", [])
        # The untested-pattern note was removed (owner decision 2026-11-19):
        # the article must not carry it. The Pattern status metadata line is
        # still stripped from the body.
        self.assertNotIn("not yet physically tested", page)
        self.assertNotIn("Pattern status:", page)

    def test_project_specific_excerpts_replace_repetitive_seo_boilerplate(self):
        curated = json.loads((ROOT / "content" / "unique_excerpts.json").read_text(encoding="utf-8"))
        manifest = set(json.loads((ROOT / "posts" / "manifest.json").read_text(encoding="utf-8")))
        self.assertEqual(len(curated), 27)
        self.assertEqual(len(set(curated.values())), len(curated))
        self.assertTrue(set(curated) <= manifest)
        for slug, summary in curated.items():
            with self.subTest(slug=slug):
                self.assertGreaterEqual(len(summary), 70)
                self.assertLessEqual(len(summary), 160)
                self.assertNotIn("component plan, counted crochet instructions", summary)
                sample = {"slug": slug, "excerpt": "Make a project with a component plan, counted crochet instructions"}
                self.assertEqual(seo_description(sample), summary)

    def test_homepage_article_fallback_matches_static_editorial_rules(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function editorialViewContent(source)", html)
        self.assertIn("display.body?articleTableOfContents(display.body)", html)
        self.assertIn("display.note?'<details class=\"article-disclosure\"", html)
        self.assertIn("dynamic-concept-cover", html)
        self.assertIn("filter(entry=>entry.level===2)", html)
        self.assertIn("['02','04','09'].includes(num)", html)

    def test_faq_schema_parses_both_question_formats(self):
        heading_style = (
            "## Materials\n\nUse cotton yarn.\n\n"
            "## Frequently Asked Questions\n\n"
            "### Do I need floral wire?\n\n"
            "Only for a bendable bouquet.\n\n"
            "### Can I sell it?\n\n"
            "Yes, you can sell the finished piece.\n"
        )
        self.assertEqual(extract_faq(heading_style), [
            ("Do I need floral wire?", "Only for a bendable bouquet."),
            ("Can I sell it?", "Yes, you can sell the finished piece."),
        ])
        bold_style = (
            "## Frequently asked questions\n\n"
            "**What yarn do I need?**\n\n"
            "Smooth cotton yarn.\n\n"
            "**How big is it?**\n\n"
            "About 20 cm tall.\n"
        )
        self.assertEqual(extract_faq(bold_style), [
            ("What yarn do I need?", "Smooth cotton yarn."),
            ("How big is it?", "About 20 cm tall."),
        ])
        self.assertEqual(extract_faq("## Materials\n\nUse cotton yarn."), [])

    def test_render_page_emits_faq_schema_only_when_faq_present(self):
        with_faq = {
            "slug": "faq-sample",
            "title": "FAQ Sample Pattern",
            "content": "## Materials\n\nUse cotton yarn.\n\n## Frequently Asked Questions\n\n### What hook do I need?\n\nA 3.5 mm hook.",
            "excerpt": "A sample pattern with a frequently asked questions section.",
        }
        page = render_page(with_faq, "body{color:#29342d}", [])
        self.assertIn('"@type": "FAQPage"', page)
        self.assertIn("What hook do I need?", page)
        without_faq = {
            "slug": "no-faq-sample",
            "title": "No FAQ Sample Pattern",
            "content": "## Materials\n\nUse cotton yarn.",
            "excerpt": "A sample pattern without any questions.",
        }
        self.assertNotIn("FAQPage", render_page(without_faq, "body{color:#29342d}", []))

    def test_related_posts_link_six_same_category_first(self):
        article = {"slug": "main", "title": "Main", "category": "Wearable Crochet"}
        others = [
            {"slug": f"same-{index}", "title": f"Same {index}", "category": "Wearable Crochet"}
            for index in range(7)
        ] + [
            {"slug": f"other-{index}", "title": f"Other {index}", "category": "Amigurumi"}
            for index in range(2)
        ]
        related = related_articles(article, others)
        self.assertEqual(len(related), 6)
        self.assertTrue(all(item["category"] == "Wearable Crochet" for item in related))
        self.assertNotIn("main", [item["slug"] for item in related])
        rendered = render_page(
            {**article, "content": "## Materials\n\nUse cotton yarn."},
            "body{color:#29342d}", [article] + others,
        )
        self.assertEqual(rendered.count('<li><a href="https://cozyloops.site/posts/'), 6)

    def test_author_resolved_by_category_and_exclusion(self):
        self.assertEqual(len(AUTHORS), 5)
        self.assertEqual(resolve_author({"slug": "x", "category": "Amigurumi"})["name"], "Emma Carter")
        self.assertEqual(resolve_author({"slug": "x", "category": "Wearable Crochet"})["name"], "Grace Miller")
        self.assertEqual(resolve_author({"slug": "x", "category": "Home Decor"})["name"], "Sophie Hayes")
        self.assertEqual(resolve_author({"slug": "x", "category": "Accessories"})["name"], "Mia Thompson")
        self.assertEqual(resolve_author({"slug": "x", "category": "Beginner Tutorials"})["name"], "Lily Bennett")
        for slug in KEEP_HOUSSAM_SLUGS:
            with self.subTest(slug=slug):
                self.assertEqual(resolve_author({"slug": slug, "category": "Amigurumi"}), HOUSSAM_AUTHOR)
        self.assertEqual(resolve_author({"slug": "x", "category": "Unknown Category"}), HOUSSAM_AUTHOR)
        self.assertEqual(resolve_author({"slug": "x"}), HOUSSAM_AUTHOR)

    def test_render_page_uses_resolved_author(self):
        amigurumi = {
            "slug": "amigurumi-sample",
            "title": "Amigurumi Sample Pattern",
            "category": "Amigurumi",
            "content": "## Materials\n\nUse cotton yarn.",
            "excerpt": "A sample amigurumi pattern with a resolved contributor author.",
        }
        page = render_page(amigurumi, "body{color:#29342d}", [])
        self.assertIn("By Emma Carter", page)
        self.assertIn('"name": "Emma Carter"', page)
        self.assertIn("https://cozyloops.site/authors/emma-carter/", page)
        self.assertIn("Emma writes CozyLoops", page)
        self.assertIn(">EC<", page)
        kept = {
            "slug": "chunky-ribbed-crochet-scarf-pattern",
            "title": "Chunky Ribbed Crochet Scarf Pattern",
            "category": "Wearable Crochet",
            "content": "## Materials\n\nUse cotton yarn.",
            "excerpt": "A sample scarf pattern that keeps Houssam as its author.",
        }
        kept_page = render_page(kept, "body{color:#29342d}", [])
        self.assertIn("By Houssam El Ouardy", kept_page)
        self.assertIn("https://cozyloops.site/about/", kept_page)

    def test_author_page_lists_its_articles(self):
        author = AUTHORS_BY_CATEGORY["Amigurumi"]
        page = render_author_page(author, self.posts, "body{color:#29342d}")
        self.assertIn("Emma Carter", page)
        self.assertIn("amigurumi patterns", page)
        self.assertIn("https://cozyloops.site/authors/emma-carter/", page)
        self.assertIn("https://cozyloops.site/posts/", page)
        for post in self.posts:
            if post.get("category") == "Amigurumi":
                self.assertIn(post["slug"], page)
            if post.get("category") == "Wearable Crochet":
                self.assertNotIn(post["slug"], page)

    def test_homepage_spa_resolves_authors(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("function resolveAuthor(p)", html)
        self.assertIn("emma-carter", html)
        self.assertIn("KEEP_HOUSSAM_SLUGS", html)
        self.assertIn("chunky-ribbed-crochet-scarf-pattern", html)
        self.assertIn(".slice(0,6)", html)
        self.assertIn("${author.initials}", html)

if __name__ == "__main__":
    unittest.main()
