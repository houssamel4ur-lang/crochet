"""Day-one editorial gate: no extra articles, no fabricated testing evidence."""
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-11-17"
SLUGS = (
    "mini-crochet-goose-bag-charm-with-embroidered-face",
    "crochet-earbud-cord-wrap-with-a-buttonhole",
)
ARTWORK = {
    SLUGS[0]: ["goose-charm-cover.svg", "goose-charm-materials.svg", "goose-charm-assembly.svg"],
    SLUGS[1]: ["earbud-wrap-cover.svg", "earbud-wrap-measurements.svg", "earbud-wrap-finished.svg"],
}


class DayOneEditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.editorials = json.loads((ROOT / "content/github_articles.json").read_text(encoding="utf8"))
        cls.manifest = json.loads((ROOT / "posts/manifest.json").read_text(encoding="utf8"))

    def test_only_the_two_day_one_editorials_are_new(self):
        today = [a for a in self.editorials if str(a.get("created_at", "")).startswith(DAY)]
        self.assertEqual({a["slug"] for a in today}, set(SLUGS))
        self.assertEqual(len(today), 2)
        self.assertEqual(len(self.manifest), len(set(self.manifest)))
        for slug in SLUGS:
            self.assertIn(slug, self.manifest)

    def test_originality_length_images_and_counted_rows(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                a = next(a for a in self.editorials if a["slug"] == slug)
                self.assertEqual(a["status"], "published")
                self.assertTrue(a["updated_at"].startswith(DAY))
                self.assertGreaterEqual(len(re.findall(r"\b[\w'-]+\b", a["content"])), 700)
                self.assertGreater(len(set(re.findall(r"(?m)^## [^\n]+", a["content"]))), 5)
                self.assertIn("##", a["content"])
                self.assertIn("Frequently asked questions" if slug == SLUGS[0] else "Questions before making a gift", a["content"])
                self.assertIn("**Editorial note:**", a["content"])
                self.assertIn("not a photograph", a["content"].lower())
                asset_dir = ROOT / "assets/day1-20261117"
                urls = [a["image_url"]] + re.findall(r"!\[[^]]*\]\((https://[^)]+)\)", a["content"])
                self.assertEqual(len(urls), 3)
                self.assertEqual(len(set(urls)), 3)
                self.assertEqual({v.split("/")[-1] for v in urls}, set(ARTWORK[slug]))
                for path in [asset_dir / name for name in ARTWORK[slug]]:
                    self.assertTrue(path.is_file(), str(path))
                    ET.parse(path)

    def test_stitch_arithmetic_and_distinct_reading_time(self):
        goose = next(x for x in self.editorials if x["slug"] == SLUGS[0])["content"]
        wrap = next(x for x in self.editorials if x["slug"] == SLUGS[1])["content"]
        for count in ("(6)", "(12)", "(18)", "(24)"):
            self.assertIn(count, goose)
        self.assertIn("Round 8", goose)
        self.assertIn("Round 9", goose)
        self.assertIn("Round 15", wrap)
        self.assertIn("Round 16", wrap)
        self.assertIn("12 single crochets", wrap)
        self.assertIn("chain 4", wrap.lower())
        goose_minutes = (len(re.findall(r"\b[\w'-]+\b", goose))+199)//200
        wrap_minutes = (len(re.findall(r"\b[\w'-]+\b", wrap))+199)//200
        self.assertNotEqual(goose_minutes, wrap_minutes)

    def test_generated_pages_have_verified_metadata_not_fake_testing(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                html = (ROOT / "posts" / slug / "index.html").read_text(encoding="utf8")
                self.assertIn("By Houssam El Ouardy", html)
                self.assertIn("Published November 17, 2026", html)
                self.assertIn("Updated November 17, 2026", html)
                self.assertIn('class="author-bio"', html)
                self.assertIn("Pattern note: This concept is not yet physically tested", html)
                self.assertGreater(html.index("Pattern note:"), html.index("##") if "##" in html else html.index("<h2"))
                self.assertNotIn("Original pattern draft — not yet physically tested", html)


if __name__ == "__main__":
    unittest.main()
