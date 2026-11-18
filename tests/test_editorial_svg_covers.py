"""Check the original 15 vector illustration covers and conservative overrides."""
import json
import re
import unittest
from pathlib import Path
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_seo import BASE, improved_editorial_cover

ASSETS = ROOT / "assets" / "editorial-illustrations"

class EditorialCovers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = sorted(ASSETS.glob("*-cover.svg"))
        cls.catalog = json.loads((ROOT / "content" / "github_articles.json").read_text(encoding="utf-8"))

    def test_exactly_fifteen_existing_editorial_slugs(self):
        self.assertEqual(len(self.files), 15)
        known = {p["slug"] for p in self.catalog}
        self.assertTrue({p.stem.removesuffix("-cover") for p in self.files} <= known)

    def test_svg_is_local_honest_accessible_and_rasterized(self):
        for source in self.files:
            with self.subTest(file=source.name):
                content = source.read_text(encoding="utf-8")
                self.assertIn('viewBox="0 0 1200 750"', content)
                self.assertIn('Original scalable editorial illustration, not a photo', content)
                self.assertIn('<title id="title">', content)
                self.assertNotIn("<script", content)
                self.assertNotIn("<foreignObject", content)
                self.assertNotRegex(content, r'(?i)(?:href|src)\s*=\s*"https?://')
                self.assertNotRegex(content, r'(?i)onload\s*=')
                with Image.open(source.with_suffix(".webp")) as cover:
                    self.assertEqual(cover.format, "WEBP")
                    self.assertEqual(cover.size, (1200, 750))
                self.assertLess(source.with_suffix(".webp").stat().st_size, 450_000)

    def test_homepage_preserves_original_article_covers(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("function upgradeDefaultEditorialCover(p)", home)
        self.assertIn("chosen.set(p.slug,p)", home)
        self.assertIn("function cardVisual(p)", home)
        self.assertIn("const defaultEditorial='https://cozyloops.site/assets/'+p.slug+'-01.webp'", home)
        self.assertEqual(home.count("hbagency_space_349628"), 2)

    def test_default_cover_is_preserved_until_validated_photo_exists(self):
        for source in self.files:
            slug = source.stem.removesuffix("-cover")
            original = {"slug": slug, "title": "A Crochet Project",
                        "image_url": f"{BASE}assets/{slug}-01.webp"}
            self.assertEqual(improved_editorial_cover(original), original)

            custom = {"slug":slug,"title":"A Crochet Project",
                      "image_url":"https://example.com/owner-custom.webp"}
            self.assertEqual(improved_editorial_cover(custom), custom)

if __name__ == "__main__":
    unittest.main()
