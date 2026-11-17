"""Regression tests for opt-in editorial-photo replacement and layout safety."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_seo


SLUG = "crochet-daisy-flower-bookmark-free-pattern"
DEFAULT = build_seo.BASE + "assets/" + SLUG + "-01.webp"


class TestPhotoReplacements(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(build_seo, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def add_photo(self, role, width=1600, height=1050):
        path = self.root / "assets" / "article-photos-v2" / SLUG / (role + ".webp")
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (width, height), "#e6d7ba").save(path, format="WEBP")
        return path

    def test_missing_photo_does_not_override_existing_image(self):
        original = {"slug": SLUG, "title": "Daisy Bookmark", "image_url": DEFAULT}
        self.assertEqual(build_seo.improved_editorial_cover(original), original)

    def test_no_thumbnail_upscaling(self):
        self.add_photo("hero", 640, 480)
        self.assertEqual(build_seo.staged_photo_url(SLUG, "hero"), "")
        original = {"slug": SLUG, "title": "Daisy Bookmark", "image_url": DEFAULT}
        self.assertEqual(build_seo.improved_editorial_cover(original), original)

    def test_large_photo_replaces_only_default_or_generated_cover(self):
        self.add_photo("hero")
        photo = build_seo.BASE + "assets/article-photos-v2/" + SLUG + "/hero.webp"
        for old in (DEFAULT, build_seo.BASE + "assets/editorial-illustrations/" + SLUG + "-cover.webp"):
            old_article = {"slug": SLUG, "title": "Daisy Bookmark", "image_url": old}
            updated = build_seo.improved_editorial_cover(old_article)
            self.assertEqual(updated["image_url"], photo)
            self.assertIn("not a photograph", updated["image_alt"])
        custom = {"slug": SLUG, "title": "Daisy Bookmark",
                  "image_url": "https://example.com/owner-photo.webp"}
        self.assertEqual(build_seo.improved_editorial_cover(custom), custom)

    def test_invalid_paths_and_roles_are_rejected(self):
        for slug in ("../private", "UPPERCASE", "", "a/other"):
            self.assertEqual(build_seo.staged_photo_url(slug, "hero"), "")
        self.assertEqual(build_seo.staged_photo_url(SLUG, "icon"), "")

    def test_stage_replaces_only_matching_editorial_image(self):
        svg = self.root / "assets" / "editorial-illustrations" / (SLUG + "-cover.svg")
        svg.parent.mkdir(parents=True, exist_ok=True)
        svg.write_text("<svg></svg>", encoding="utf-8")
        self.add_photo("materials")
        src = f"![old]({build_seo.BASE}assets/{SLUG}-02.webp)"
        other = "![Owner upload](https://example.com/custom.webp)"
        result = build_seo.crisp_concept_panels(src + "\n\n" + other, SLUG)
        self.assertIn("/article-photos-v2/" + SLUG + "/materials.webp", result)
        self.assertIn(other, result)
        self.assertNotIn("assets/" + SLUG + "-02.webp", result)


if __name__ == "__main__":
    unittest.main()
