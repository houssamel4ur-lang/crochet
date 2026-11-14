"""Regression checks for SEO, readable article layouts, and safe publishing."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("build_seo", ROOT / "scripts/build_seo.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

class EditorialQualityTests(unittest.TestCase):
    def test_description_has_clean_limit(self):
        self.assertLessEqual(len(build.seo_description({"excerpt": "Crochet flowers " * 30})), 160)
        self.assertEqual(build.seo_description({"excerpt": "Handmade tulip bouquet."}), "Handmade tulip bouquet.")

    def test_toc_excludes_question_headings_and_preserves_anchors(self):
        source = "## Materials\n### Which hook?\n## Instructions\n### How long?\n## Finish"
        toc = build.table_of_contents(source)
        self.assertIn('href="#section-1"', toc)
        self.assertIn('href="#section-3"', toc)
        self.assertIn('href="#section-5"', toc)
        self.assertNotIn("Which hook?", toc)
        self.assertIn("<details", toc)

    def test_disclosure_is_relocated_not_deleted(self):
        source = ("Welcome!\n\n**Editorial note:** Images are AI-generated and not real samples.\n\n"
                  "## Materials\nUse a hook.")
        body, note = build.normalize_article_content(source)
        self.assertNotIn("Editorial note", body)
        self.assertIn("AI-generated", note)
        self.assertIn("## Materials", body)

    def test_concept_images_keep_three_panels_and_original_content_unchanged(self):
        images = "\n\n".join(
            f"![step {i}](https://cozyloops.site/assets/crochet-tulip-bouquet-stems-guide-{i:02d}.webp)"
            for i in range(1, 10))
        result = build.concise_editorial_illustrations(images)
        self.assertEqual(result.count("!["), 3)
        for number in ("02", "04", "09"):
            self.assertIn(f"guide-{number}.webp", result)
        self.assertEqual(images.count("!["), 9)

    def test_security_pipeline_applies_csp_after_rebuild(self):
        workflow = (ROOT / ".github/workflows/update-seo-pages.yml").read_text()
        self.assertLess(workflow.index("python scripts/build_seo.py"),
                        workflow.index("python scripts/security_policy.py"))

if __name__ == "__main__":
    unittest.main()
