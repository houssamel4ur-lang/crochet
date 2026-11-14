#!/usr/bin/env python3
"""Read-only editorial audit for all published CozyLoops pages.
No invented SEO score; flag factual missing assets and review-only issues.
"""
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://cozyloops.site"
MANIFEST = ROOT / "posts" / "manifest.json"
CATALOG = ROOT / "content" / "github_articles.json"
OUTPUT = ROOT / ".github" / "editorial-quality-audit.md"

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.links = []
        self.descriptions = []
        self.canonicals = []
        self.h1 = 0
        self.toc = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img": self.images.append(a)
        if tag == "a": self.links.append(a.get("href", ""))
        if tag == "h1": self.h1 += 1
        if tag == "meta" and a.get("name") == "description": self.descriptions.append(a.get("content",""))
        if tag == "link" and a.get("rel") == "canonical": self.canonicals.append(a.get("href",""))
        if tag == "details" and a.get("class") == "article-toc": self.toc = True

def local_image(url):
    if not url: return None
    parts = urlsplit(url)
    if parts.hostname != "cozyloops.site" or parts.scheme != "https": return None
    path = unquote(parts.path).lstrip("/")
    if not path.startswith("assets/") or ".." in Path(path).parts: return None
    target = ROOT / path
    if not target.resolve().is_relative_to((ROOT / "assets").resolve()): return None
    return target

def audit():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(manifest, list) or not manifest: raise RuntimeError("Missing published manifest")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    c_by_slug = {p["slug"]:p for p in catalog if isinstance(p,dict) and p.get("slug")}
    report_rows = []
    totals = Counter()
    problems = []
    for slug in sorted(manifest):
        path = ROOT / "posts" / slug / "index.html"
        if not path.exists():
            problems.append(f"Missing generated article: {slug}")
            continue
        page = Page()
        html = path.read_text(encoding="utf-8")
        page.feed(html)
        issues = []
        expected = f"{BASE}/posts/{slug}/"
        if page.h1 != 1: issues.append("H1 count")
        if page.canonicals != [expected]: issues.append("Canonical")
        if len(page.descriptions) != 1 or not 55 <= len(page.descriptions[0]) <= 165:
            issues.append("Description review")
        if not page.images: issues.append("No cover")
        for image in page.images:
            if not image.get("alt","").strip(): issues.append("Missing image alt")
            if not image.get("width") or not image.get("height"): issues.append("Image dimensions")
            src = image.get("src","")
            if not src.startswith("https://"): issues.append("Insecure image URL")
            local = local_image(src)
            if local is not None and not local.is_file():
                issues.append("Missing local image")
        for link in page.links:
            parts = urlsplit(link)
            if parts.scheme == "https" and parts.hostname == "cozyloops.site" and parts.path.startswith("/posts/"):
                target = parts.path.split("/")
                if len(target)>2 and target[2] and target[2] not in manifest:
                    issues.append("Broken internal article link")
        source = c_by_slug.get(slug, {})
        is_ai = "AI-generated editorial" in source.get("content","")
        has_toc = page.toc
        if is_ai:
            totals["ai"] += 1
            issues.append("Concept imagery: replace with real source photo before claiming a tested pattern")
            if "article-disclosure" not in html: issues.append("Missing concept disclosure")
        if source and len(source.get("content","").split()) < 800:
            issues.append("Short source article: editorial review")
        # The source's tiled contact sheets contain relatively small photos. This
        # is a provenance warning, not an automatic image-quality judgment.
        if slug in c_by_slug and slug in set(p["slug"] for p in catalog[:15]):
            issues.append("Contact-sheet crop: higher-resolution original needed")
        for issue in set(issues):
            totals[issue] += 1
        label = "; ".join(sorted(set(issues))) if issues else "No automated issues found"
        report_rows.append((slug,len(page.images),"yes" if has_toc else "no",label))
    lines = [
        "# CozyLoops — Article quality audit",
        "",
        "Generated automatically from current static pages and the GitHub editorial catalog.",
        "This audit verifies technical properties; it **cannot certify** visual sharpness, pattern accuracy, copyright, or security.",
        "",
        f"Articles checked: **{len(report_rows)}**. Missing generated articles: **{len(problems)}**.",
        f"Articles with AI/editorial illustration provenance: **{totals['ai']}**.",
        "",
        "| Article | Rendered images | Compact TOC | Editorial / technical findings |",
        "|---|---:|---|---|",
    ]
    for slug, count, toc, issues in report_rows:
        lines.append(f"| [`{slug}`](https://cozyloops.site/posts/{slug}/) | {count} | {toc} | {issues.replace('|','/')} |")
    lines.extend(["","## Automated findings", ""])
    for issue,count in sorted(totals.items()):
        if issue == "ai": continue
        lines.append(f"- **{count}** article(s): {issue}")
    lines.extend(["","## Checks that still require a real person or direct infrastructure access", "",
        "- Compare EVERY crochet instruction with a physically crocheted sample before claiming it is tested",
        "- Replace low-resolution contact-sheet crops with original high-resolution project photographs",
        "- Confirm the Supabase project's RLS, storage policies, and privileged function grants",
        "- Inspect actual HTTP response headers and Cloudflare/WAF deployment, not just repository examples",
        "- Verify that the ad consent provider is compliant and has no ongoing browser errors",
        ""])
    if problems:
        lines.extend(["## Missing generated files", ""] + ["- "+p for p in problems])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("Audited",len(report_rows),"articles; warnings",dict(totals))
    if problems or totals["Missing local image"] or totals["Missing image alt"] or totals["Canonical"] or totals["Broken internal article link"]:
        return 1
    return 0

if __name__ == "__main__": sys.exit(audit())
