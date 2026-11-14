#!/usr/bin/env python3
"""Rasterize original scalable article illustrations into social-preview-ready WebP.

Only local, repository-authored SVG source files are processed. These graphics are
illustrations, not photographs or verified real-world crochet samples.
"""
from io import BytesIO
from pathlib import Path
from PIL import Image
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
COVERS = ROOT / "assets" / "editorial-illustrations"

def main():
    source_files = sorted(COVERS.glob("*-cover.svg"))
    if len(source_files) != 15:
        raise RuntimeError(f"Expected 15 curated SVG illustrations, got {len(source_files)}")
    for source in source_files:
        raw = source.read_text(encoding="utf-8")
        if ('viewBox="0 0 1200 750"' not in raw or
                'not a photo or physically tested crochet sample' not in raw):
            raise ValueError(f"Invalid provenance or size: {source.name}")
        png = cairosvg.svg2png(bytestring=raw.encode("utf-8"), output_width=1200, output_height=750)
        with Image.open(BytesIO(png)) as artwork:
            rgb = artwork.convert("RGB")
            target = source.with_suffix(".webp")
            rgb.save(target, "WEBP", quality=89, method=6)
            if target.stat().st_size > 450_000:
                raise RuntimeError(f"Oversized illustration: {target.name}")
    print(f"Rasterized {len(source_files)} original editorial illustrations (1200 x 750 WebP)")

if __name__ == "__main__":
    main()
