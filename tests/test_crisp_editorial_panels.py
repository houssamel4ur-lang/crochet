"""Ensure the 15 former low-res crop articles have honest, scalable inline diagrams."""
from pathlib import Path
from xml.etree import ElementTree as ET
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "assets" / "editorial-illustrations"

class CrispEditorialPanelTests(unittest.TestCase):
    def test_every_concept_article_has_three_scalable_visuals(self):
        covers = sorted(DIR.glob("*-cover.svg"))
        self.assertEqual(len(covers), 15)
        expected = [DIR / f"{cover.name.removesuffix('-cover.svg')}-panel-{n}.svg"
                    for cover in covers for n in ("02", "04", "09")]
        self.assertEqual(len(expected), 45)
        for path in expected:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), f"Missing vector diagram {path.name}")
                source = path.read_text(encoding="utf-8")
                root = ET.fromstring(source)
                self.assertEqual(root.attrib["viewBox"], "0 0 900 1120")
                self.assertIn("not a real photograph", source.lower())
                self.assertIn("FOLLOW THE WRITTEN INSTRUCTIONS", source)
                self.assertNotIn("data:image/", source)
                self.assertNotIn("<image", source)

if __name__ == "__main__":
    unittest.main()
