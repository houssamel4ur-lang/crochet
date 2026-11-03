#!/usr/bin/env python3
"""Generate crawlable CozyLoops article pages from published Supabase articles.

Runs in GitHub Actions, uses only Python stdlib and the public publishable key.
It never modifies the articles database. Missing API access fails the build safely.
"""
import html
import json
import os
from pathlib import Path
import re
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://houssamel4ur-lang.github.io/crochet/"
API = "https://yqmrunstyhrhnvxoyrap.supabase.co/rest/v1/articles"
KEY = "sb_publishable_HqkcpvBz8P8KJTZFgefrWQ_rFxKPMNh"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IMAGE = re.compile(r"!\[([^\]]*)\]\((https://[^\s)]+)\)")
BOLD = re.compile(r"\*\*(.+?)\*\*")

def esc(value):
    return html.escape(str(value or ""), quote=True)

def safe_image(url):
    """Allow absolute HTTPS images with a valid host and without unsafe controls."""
    if not isinstance(url, str) or not url or any(ord(c) < 33 or ord(c) == 127 for c in url):
        return ""
    if any(c in url for c in '<>"\\'):
        return ""
    try:
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
            return ""
        if parts.port is not None and parts.port != 443:
            return ""
        return url
    except ValueError:
        return ""

def inline(value):
    output = []
    pos = 0
    for match in IMAGE.finditer(value):
        output.append(BOLD.sub(r"<strong>\1</strong>", esc(value[pos:match.start()])))
        url = safe_image(match.group(2))
        if url:
            output.append(f'<figure><img loading="lazy" decoding="async" src="{esc(url)}" alt="{esc(match.group(1))}" width="1000" height="625"></figure>')
        pos = match.end()
    output.append(BOLD.sub(r"<strong>\1</strong>", esc(value[pos:])))
    return "".join(output)

def table_of_contents(source):
    """Build accessible jump links for Markdown headings without external parsers."""
    headings = []
    for line in (source or "").splitlines():
        match = re.match(r"^#{1,3}\s+(.+)$", line.strip())
        if match:
            headings.append(match.group(1))
    if len(headings) < 2:
        return ""
    links = "".join(
        f'<li><a href="#section-{i}">{esc(title.replace('**', ''))}</a></li>'
        for i, title in enumerate(headings, 1)
    )
    return f'<nav class="article-toc" aria-label="On this page"><strong>On this page</strong><ol>{links}</ol></nav>'


def markdown(source):
    blocks = re.split(r"\n\s*\n", (source or "").strip())
    rendered = []
    heading_index = 0
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if all(line.startswith(("- ", "* ")) for line in lines):
            rendered.append("<ul>" + "".join(f"<li>{inline(line[2:])}</li>" for line in lines) + "</ul>")
            continue
        for line in lines:
            heading = re.match(r"^(#{1,3})\s+(.+)$", line)
            if heading:
                level = min(4, max(2, len(heading.group(1))))
                heading_index += 1
                rendered.append(f'<h{level} id="section-{heading_index}">{inline(heading.group(2))}</h{level}>')
            else:
                rendered.append(f"<p>{inline(line)}</p>")
    return "\n".join(rendered)

def load_articles():
    url = API + "?status=eq.published&select=title,slug,content,excerpt,image_url,category,created_at,updated_at&order=created_at.desc&limit=1000"
    req = Request(url, headers={"apikey": KEY, "Accept": "application/json", "User-Agent": "CozyLoopsStaticBuilder/1.0"})
    with urlopen(req, timeout=25) as response:
        items = json.load(response)
    if not isinstance(items, list):
        raise RuntimeError("Expected a JSON list from Supabase")
    return [p for p in items if isinstance(p.get("slug"), str) and SLUG.fullmatch(p["slug"]) and p.get("title")]

def related_articles(article, articles, limit=3):
    """Select other posts, prioritizing the same category."""
    others = [item for item in articles
              if item.get("slug") != article.get("slug")
              and isinstance(item.get("slug"), str) and SLUG.fullmatch(item["slug"])
              and isinstance(item.get("title"), str) and item["title"].strip()]
    others.sort(key=lambda item: item.get("category") != article.get("category"))
    return others[:limit]


def render_related(article, articles):
    suggestions = related_articles(article, articles)
    if not suggestions:
        return ""
    links = "".join(
        f'<li><a href="{BASE}posts/{quote(item["slug"])}/">{esc(item["title"])}</a></li>'
        for item in suggestions
    )
    return f'<section class="related-posts" aria-label="Related crochet articles"><h2>Read Next</h2><ul>{links}</ul></section>'


def render_page(article, css, articles=None):
    slug = article["slug"]
    title = str(article["title"])
    description = str(article.get("excerpt") or "")[:280]
    canonical = BASE + "posts/" + quote(slug) + "/"
    cover = safe_image(article.get("image_url"))
    category = str(article.get("category") or "Crochet Patterns")
    related_html = render_related(article, articles or [])
    toc_html = table_of_contents(str(article.get("content") or ""))
    published = str(article.get("created_at") or "")
    modified = str(article.get("updated_at") or published)
    structured = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": description,
        "mainEntityOfPage": canonical,
        "url": canonical,
        "publisher": {"@type": "Organization", "name": "CozyLoops"},
        "datePublished": published,
        "dateModified": modified,
        "articleSection": category,
    }
    if cover:
        structured["image"] = cover
    image_html = f'<img class="article-cover" src="{esc(cover)}" alt="{esc(title)}" width="1000" height="625" fetchpriority="high" decoding="async">' if cover else ""
    structured_json = json.dumps(structured, ensure_ascii=False).replace("<", "\\u003c")
    social_image = f'<meta property="og:image" content="{esc(cover)}">' if cover else ""
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | CozyLoops</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{esc(canonical)}">
<link rel="icon" type="image/svg+xml" href="{BASE}favicon.svg">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
{social_image}
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{structured_json}</script>
<script defer src="{BASE}scripts/article_analytics.js"></script>
<style>{css}
.article-cover{{max-height:520px;width:100%;height:auto;aspect-ratio:16/10;object-fit:cover;border-radius:18px}}
.article figure{{margin:22px 0}}.article figure img{{width:100%;height:auto;border-radius:15px}}
.article ul{{padding-left:26px}}.article strong{{font-weight:700}}
.related-posts{{margin:32px 0;padding:22px;border:1px solid var(--line,#e5e7df);border-radius:16px;background:var(--white,#fff)}}
.article-toc{{padding:20px 24px;border:1px solid var(--line,#e5e7df);border-radius:16px;background:var(--white,#fff);margin:24px 0}}.article-toc ol{{margin:8px 0 0;padding-left:24px}}.article-toc li{{margin:5px 0}}.article-toc a{{text-decoration:underline;text-underline-offset:3px}}.article h2[id],.article h3[id],.article h4[id]{{scroll-margin-top:24px}}
.related-posts ul{{margin:12px 0 0;padding-left:22px}}.related-posts li{{margin:8px 0}}.related-posts a{{text-decoration:underline;text-underline-offset:3px}}
.article-share{{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:10px 0 24px}}.article-share-button{{border:1px solid var(--green,#4f694c);background:transparent;color:var(--green,#4f694c);border-radius:25px;padding:8px 16px;font:600 14px/1.4 system-ui,sans-serif;cursor:pointer}}.article-share-button:hover,.article-share-button:focus-visible{{background:var(--green,#4f694c);color:white}}#article-share-status{{font-size:14px;color:var(--muted,#68736a)}}
.article-print-button{{border:1px solid var(--line,#e5e7df);background:var(--white,#fff);color:var(--ink,#29342d);border-radius:25px;padding:8px 16px;font:600 14px/1.4 system-ui,sans-serif;cursor:pointer}}.article-print-button:hover,.article-print-button:focus-visible{{border-color:var(--green,#4f694c);color:var(--green,#4f694c)}}
@media print{{@page{{margin:16mm}}html,body{{background:white!important;color:#111!important;font:11pt/1.45 Georgia,serif!important}}header,footer,.back,.article-share,.article-toc,.related-posts,.article-privacy,.privacy-choice,.skip-link{{display:none!important}}main#content{{display:block!important;padding:0!important;margin:0!important}}.article{{max-width:none!important;width:100%!important;margin:0!important;padding:0!important;box-shadow:none!important;border:0!important;background:white!important}}.article-cover{{display:none!important}}.article h1{{font-size:24pt!important;margin:0 0 12pt!important}}.article h2{{font-size:16pt!important}}.article h3{{font-size:13pt!important}}.article h2,.article h3,.article h4{{break-after:avoid}}.article p,.article li{{orphans:3;widows:3}}.article figure img{{max-width:100%!important;height:auto!important;break-inside:avoid}}.article a{{color:#111!important;text-decoration:none!important}}.article>.btn{{display:none!important}}}}
.reading-progress{{position:fixed;z-index:60;top:0;left:0;width:100%;height:4px;pointer-events:none;background:transparent}}.reading-progress span{{display:block;width:100%;height:100%;background:var(--green,#4f694c);transform:scaleX(0);transform-origin:left center;transition:transform .08s linear}}
@media print{{.reading-progress{{display:none!important}}}}
</style>
</head>
<body>
<a class="skip-link" href="#content">Skip to content</a>
<header><nav class="nav"><a class="brand" href="{BASE}">CozyLoops ♡</a><div class="links"><a href="{BASE}">Home</a><a href="{BASE}#articles">Articles</a><a href="{BASE}#categories">Categories</a></div></nav></header>
<div class="reading-progress" aria-hidden="true"><span></span></div>
<main id="content"><article class="article">
<a class="back" href="{BASE}#articles">← Back to all articles</a>
<div class="tag">{esc(category)}</div>
<h1>{esc(title)}</h1>
<p class="meta">{esc(published[:10])} · CozyLoops</p>
<div class="article-share"><button type="button" id="article-share-button" class="article-share-button">Share this article</button><button type="button" id="article-print-button" class="article-print-button">Print / Save PDF</button><span id="article-share-status" role="status" aria-live="polite"></span></div>
<p>{esc(description)}</p>
{image_html}
{toc_html}
{markdown(str(article.get("content") or ""))}
{related_html}
<h2>Keep Creating</h2>
<p>Explore more crochet articles and patterns at CozyLoops.</p>
<a class="btn" href="{BASE}#articles">Browse all articles</a>
<section class="article-privacy" aria-label="Analytics preferences"><h2>Analytics preferences</h2><p id="article-consent-status" role="status">You can disable optional analytics for this browser at any time.</p><button type="button" id="article-privacy-opt-out" class="btn">Disable optional analytics</button></section>
</article></main>
<aside id="privacy-choice" class="privacy-choice" aria-label="Optional article analytics" hidden><strong>Help us improve CozyLoops?</strong><p>With your permission, we count this article view once per browser per day. We store no names, emails or IP addresses in our analytics table. You can decline and keep reading.</p><div class="actions"><button type="button" id="privacy-decline">No thanks</button><button type="button" class="accept" id="privacy-accept">Allow analytics</button></div></aside>
<footer><div class="footer-inner"><div><a class="brand" href="{BASE}">CozyLoops ♡</a><p>Slow down, pick up your yarn, and create something lovely.</p></div><div><a href="{BASE}#about">About</a><a href="{BASE}#contact">Contact</a><a href="{BASE}#privacy">Privacy</a></div></div></footer>
</body></html>
'''

def main():
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    found = re.search(r"<style>(.*?)</style>", source, re.S)
    if not found:
        raise RuntimeError("Homepage stylesheet missing")
    css = found.group(1)
    articles = load_articles()
    output_root = ROOT / "posts"
    output_root.mkdir(exist_ok=True)
    manifest = output_root / "manifest.json"
    legacy_manifest = output_root / ".generated_slugs.json"
    try:
        previous = json.loads(manifest.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        try:
            previous = json.loads(legacy_manifest.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            previous = []
    current = []
    sitemap = [BASE]
    for item in articles:
        slug = item["slug"]
        current.append(slug)
        page_dir = output_root / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(render_page(item, css, articles), encoding="utf-8")
        sitemap.append(BASE + "posts/" + slug + "/")
    for slug in previous:
        if isinstance(slug, str) and SLUG.fullmatch(slug) and slug not in current:
            old = output_root / slug / "index.html"
            if old.exists():
                old.unlink()
                try: old.parent.rmdir()
                except OSError: pass
    manifest.write_text(json.dumps(sorted(current), indent=2) + "\n", encoding="utf-8")
    if legacy_manifest.exists():
        legacy_manifest.unlink()
    xml = '<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "".join("  <url><loc>" + esc(url) + "</loc></url>\n" for url in sitemap)
    xml += "</urlset>\n"
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"Generated {len(current)} SEO article pages and sitemap entries")

if __name__ == "__main__":
    main()
