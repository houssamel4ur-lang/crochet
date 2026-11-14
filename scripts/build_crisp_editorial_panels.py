#!/usr/bin/env python3
"""Build crisp, original SVG references instead of enlarging tiny contact-sheet crops.

This renders three illustrated reference cards per existing 15-article editorial
series from its OWN hand-authored SVG cover artwork. These are NOT photographs,
and cannot verify physical stitch shapes, fit, or the accuracy of a pattern.
Legacy photo assets and the original article content remain untouched.
"""
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import textwrap
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
COVERS = ROOT / "assets" / "editorial-illustrations"
CATALOG = ROOT / "content" / "github_articles.json"
NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", "http://www.w3.org/2000/svg")

STAGES = {
    "02": (
        "Materials at a glance",
        ("Follow the yarn and hook notes", "Keep a stitch marker nearby", "Make a gauge swatch first"),
        "#527762", "#D9E7D8",
    ),
    "04": (
        "Start the construction",
        ("Follow the written stitch counts", "Mark the start of each round", "Check the shaping as you go"),
        "#A26D77", "#F2DFE2",
    ),
    "09": (
        "Finish with care",
        ("Align parts before joining", "Secure and weave in yarn ends", "Check the finished measurements"),
        "#8C714F", "#EEE4D2",
    ),
}


def create_panels():
    posts = json.loads(CATALOG.read_text(encoding="utf-8"))
    titles = {row["slug"]: row["title"] for row in posts if isinstance(row, dict) and "slug" in row}
    source_covers = sorted(COVERS.glob("*-cover.svg"))
    if len(source_covers) != 15:
        raise RuntimeError(f"Expected 15 original project illustrations; found {len(source_covers)}")
    count = 0
    for source in source_covers:
        slug = source.name.removesuffix("-cover.svg")
        if slug not in titles:
            raise RuntimeError(f"Missing matching article in editorial catalog: {slug}")
        root = ET.parse(source).getroot()
        # The product illustration, not the text or paper background, is reused.
        artwork = next(
            (g for g in root.findall(f"{NS}g")
             if g.attrib.get("transform", "").startswith("translate(742 133)")), None
        )
        if artwork is None:
            raise RuntimeError(f"Missing original project artwork: {source.name}")
        artwork_xml = ET.tostring(deepcopy(artwork), encoding="unicode")
        title_lines = textwrap.wrap(titles[slug].replace(" — ", ": "), width=30)
        title_lines = title_lines[:3] if title_lines else ["Crochet project"]
        for number, (heading, bullets, color, tint) in STAGES.items():
            title_markup = "".join(
                f'<text x="66" y="{309+46*i}" font-family="Georgia,serif" '
                f'font-size="34" font-weight="700" fill="#304439">{escape(line)}</text>'
                for i, line in enumerate(title_lines)
            )
            bullet_markup = "".join(
                f'<text x="99" y="{465+58*i}" font-family="Arial,sans-serif" '
                f'font-size="29" fill="#46584C">{escape(line)}</text>'
                f'<circle cx="77" cy="{455+58*i}" r="5" fill="{color}"/>'
                for i, line in enumerate(bullets)
            )
            body = f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1120"
viewBox="0 0 900 1120" role="img" aria-labelledby="title desc">
<title id="title">{escape(heading)} — {escape(titles[slug])}</title>
<desc id="desc">Original scalable editorial concept illustration. Not a real photograph or a tested crochet step.</desc>
<defs><linearGradient id="paper" x1="0" x2="1" y1="0" y2="1">
<stop stop-color="#FFFDF9"/><stop offset="1" stop-color="#F3F3EA"/>
</linearGradient></defs>
<rect width="900" height="1120" fill="url(#paper)"/>
<path d="M0 1000 Q330 958 620 1012 T900 994 L900 1120 H0Z" fill="{tint}" opacity=".36"/>
<circle cx="460" cy="858" r="259" fill="{tint}" opacity=".62"/>
<circle cx="460" cy="858" r="239" fill="#FFFCF7" stroke="{color}" stroke-opacity=".2" stroke-width="2"/>
<rect x="35" y="35" width="830" height="609" rx="25" fill="#FFFEFC" stroke="#E1E8DD" stroke-width="2"/>
<path d="M72 135 H829" stroke="#E4E9E0" stroke-width="2"/>
<text x="66" y="94" font-family="Arial,sans-serif" font-size="19"
letter-spacing="3" font-weight="700" fill="{color}">COZYLOOPS  /  ILLUSTRATED GUIDE</text>
<text x="66" y="221" font-family="Georgia,serif" font-size="49"
font-weight="700" fill="#304439">{escape(heading)}</text>
<path d="M68 240 H235" stroke="{color}" stroke-width="6" stroke-linecap="round"/>
{title_markup}
{bullet_markup}
<g transform="translate(-530 500) scale(1.05)">{artwork_xml}</g>
<text x="66" y="1080" font-family="Arial,sans-serif" font-size="17" fill="#667668">
CONCEPT VISUAL · FOLLOW THE WRITTEN INSTRUCTIONS</text>
</svg>
"""
            target = COVERS / f"{slug}-panel-{number}.svg"
            if not target.is_file() or target.read_text(encoding="utf-8") != body:
                target.write_text(body, encoding="utf-8")
            count += 1
    print(f"Prepared {count} crisp original vector step panels for {len(source_covers)} articles.")


if __name__ == "__main__":
    create_panels()
