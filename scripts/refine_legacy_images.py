#!/usr/bin/env python3
"""Rework existing CozyLoops legacy photos without inventing new stitch details.

The images come exclusively from this repository. Original photos are left unchanged.
Only covers are updated; tutorial step images remain available in the articles.
"""
from pathlib import Path
import json
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TARGET = ASSETS / "legacy-polished"
CATALOG = ROOT / "content" / "github_articles.json"
LEGACY = {
    "easy-crochet-scarf-for-beginners": "easy-crochet-scarf-for-beginners",
    "capybara-amigurumi-free-crochet-pattern": "capybara-amigurumi-free-crochet-pattern",
    "daisy-granny-square-blanket-guide": "daisy-granny-square-blanket-guide",
    "crochet-plant-hanger-beginners": "crochet-plant-hanger-beginners",
    "crochet-bucket-hat-for-beginners": "crochet-bucket-hat-for-beginners",
    "sunflower-crochet-tote-bag-guide": "sunflower-crochet-tote-bag-guide",
    "easy-crochet-beanie-pattern": "easy-crochet-beanie-pattern",
}
OUTPUT_SIZE = (1200, 720)

def finish(im):
    im = ImageEnhance.Contrast(im).enhance(1.035)
    im = ImageEnhance.Color(im).enhance(1.025)
    return im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=75, threshold=4))

def polish_regular(source):
    with Image.open(source) as base:
        base = base.convert("RGB")
        width, height = base.size
        # Remove the thin decorative/blurred outer frame, not the crochet itself.
        cut = max(2, round(width * 0.028))
        top = max(2, round(height * 0.025))
        base = base.crop((cut, top, width - cut, height - top))
        return finish(ImageOps.fit(base, OUTPUT_SIZE, method=Image.Resampling.LANCZOS,
                                   centering=(0.5, 0.48)))

def polish_scarf():
    """Original scarf shots have blurred side panels and a sharp portrait centre.
    Reuse all three clear centres in one full-width editorial triptych.
    No pixel detail is hallucinated and the source photos remain unchanged.
    """
    canvas = Image.new("RGB", OUTPUT_SIZE, "#f8f5ef")
    gap = 13
    tile_width = (OUTPUT_SIZE[0] - 4 * gap) // 3
    tile_height = OUTPUT_SIZE[1] - 2 * gap
    for index in (1, 2, 3):
        path = ASSETS / f"easy-crochet-scarf-for-beginners-{index}.webp"
        with Image.open(path) as original:
            original = original.convert("RGB")
            w, h = original.size
            # The portrait was composed between approximately 34%-66% of frame.
            photo = original.crop((round(w * .345), round(h * .008),
                                   round(w * .655), round(h * .992)))
            photo = ImageOps.fit(photo, (tile_width, tile_height),
                                 method=Image.Resampling.LANCZOS)
            photo = finish(photo)
            mask = Image.new("L", (tile_width, tile_height), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, tile_width-1, tile_height-1), radius=10, fill=255)
            left = gap + (index-1) * (tile_width + gap)
            canvas.paste(photo, (left, gap), mask)
    return canvas

def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    processed = 0
    for article in catalog:
        slug = article.get("slug")
        if slug not in LEGACY or article.get("status") != "published":
            continue
        origin = ASSETS / (LEGACY[slug] + "-1.webp")
        if not origin.is_file():
            raise FileNotFoundError(f"Legacy photo missing: {origin}")
        cover = polish_scarf() if slug == "easy-crochet-scarf-for-beginners" else polish_regular(origin)
        target = TARGET / (slug + "-cover.webp")
        temp = target.with_suffix(".tmp.webp")
        cover.save(temp, "WEBP", quality=88, method=6)
        if not target.exists() or target.read_bytes() != temp.read_bytes():
            temp.replace(target)
        else:
            temp.unlink()
        article["image_url"] = "https://cozyloops.site/assets/legacy-polished/" + target.name
        if slug == "easy-crochet-scarf-for-beginners":
            article["image_alt"] = "Three clear views of the sage crochet scarf: finished scarf, stitching detail, and scarf on a chair"
        processed += 1
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {processed} polished legacy article covers. Original tutorial images are unchanged.")

if __name__ == "__main__":
    main()
