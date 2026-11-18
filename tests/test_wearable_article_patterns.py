import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "content" / "github_articles.json").read_text(encoding="utf-8"))

def article(slug):
    return next(item for item in CATALOG if item.get("slug") == slug)["content"]

class TestWearableArticlePatternCounts(unittest.TestCase):
    def test_granny_square_has_four_corners_and_four_side_spaces(self):
        text = article("crochet-granny-square-vest-and-striped-summer-top")
        self.assertIn("four 3-dc groups separated by four corner ch-2 spaces", text)
        self.assertIn("one ch-1 side space between each pair of corners", text)
        self.assertIn("3 dc in the final ch-1 side space", text)

    def test_striped_top_uses_an_even_foundation_and_keeps_mesh_count(self):
        text = article("crochet-granny-square-vest-and-striped-summer-top")
        self.assertIn("Chain an even number of stitches (a multiple of 2).", text)
        self.assertIn("without increasing the stitch count", text)
        self.assertNotIn("Chain a multiple of 2 plus 1.", text)

    def test_pink_fan_stitch_foundation_leaves_a_complete_repeat(self):
        text = article("crochet-burgundy-peplum-and-pink-lace-crop-top")
        self.assertIn("Chain a multiple of 4 plus 2.", text)
        self.assertNotIn("Chain a multiple of 4 plus 1.", text)

if __name__ == "__main__":
    unittest.main()
