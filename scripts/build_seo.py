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
from hb_placements import inject_hb_ads
from urllib.request import Request, urlopen
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://cozyloops.site/"
API = "https://yqmrunstyhrhnvxoyrap.supabase.co/rest/v1/articles"
KEY = "sb_publishable_HqkcpvBz8P8KJTZFgefrWQ_rFxKPMNh"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IMAGE = re.compile(r"!\[([^\]]*)\]\((https://[^\s)]+)\)")
BOLD = re.compile(r"\*\*(.+?)\*\*")
LINK = re.compile(r"\[([^\]]+)\]\((https://[^\s)]+)\)")

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

def linked_text(value):
    """Parse editor-authored HTTPS Markdown links without allowing arbitrary HTML."""
    output = []
    pos = 0
    for match in LINK.finditer(value):
        output.append(BOLD.sub(r"<strong>\1</strong>", esc(value[pos:match.start()])))
        url = safe_image(match.group(2))
        if url:
            output.append(f'<a href="{esc(url)}" rel="noopener noreferrer">{esc(match.group(1))}</a>')
        else:
            output.append(esc(match.group(0)))
        pos = match.end()
    output.append(BOLD.sub(r"<strong>\1</strong>", esc(value[pos:])))
    return "".join(output)


def image_size(url):
    """Use native dimensions for local media to prevent unnecessary layout shifts."""
    try:
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.hostname == "cozyloops.site" and parsed.path.startswith("/assets/"):
            path = ROOT / parsed.path.lstrip("/")
            if path.is_file() and path.resolve().is_relative_to((ROOT / "assets").resolve()):
                from PIL import Image  # Publishing workflow dependency; optional for lightweight tests.
                with Image.open(path) as pic:
                    width, height = pic.size
                if 0 < width <= 16000 and 0 < height <= 16000:
                    return width, height
    except (OSError, ImportError, ValueError):
        pass
    return 1000, 625

def inline(value):
    output = []
    pos = 0
    for match in IMAGE.finditer(value):
        output.append(linked_text(value[pos:match.start()]))
        url = safe_image(match.group(2))
        if url:
            width, height = image_size(url)
            output.append(f'<figure><img loading="lazy" decoding="async" src="{esc(url)}" alt="{esc(match.group(1))}" width="{width}" height="{height}"></figure>')
        pos = match.end()
    output.append(linked_text(value[pos:]))
    return "".join(output)

def table_of_contents(source):
    """Compact optional navigation: only main sections, never 16 FAQ subquestions."""
    headings = []
    all_heading_number = 0
    for line in (source or "").splitlines():
        match = re.match(r"^(#{1,3})\s+(.+)$", line.strip())
        if not match:
            continue
        all_heading_number += 1
        if len(match.group(1)) == 2:
            headings.append((all_heading_number, match.group(2)))
    if len(headings) < 2:
        return ""
    links = "".join(
        f'<li><a href="#section-{number}">{esc(title.replace("**", ""))}</a></li>'
        for number, title in headings
    )
    return ('<details class="article-toc"><summary>On this page — jump to a section</summary>'
            '<nav aria-label="Article sections"><ol>' + links + '</ol></nav></details>')


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

REMOVED_STARTER_SLUGS = {'crochet-for-absolute-beginners','how-to-read-crochet-patterns','easy-crochet-scarf-guide','amigurumi-basics','choosing-crochet-yarn','crochet-stitch-counting'}

def improved_editorial_cover(item):
    """Replace only default low-res contact-sheet covers; retain owner Admin choices."""
    slug = item.get("slug", "")
    if not isinstance(slug, str) or not SLUG.fullmatch(slug):
        return item
    default = BASE + "assets/" + slug + "-01.webp"
    improved = ROOT / "assets" / "editorial-illustrations" / (slug + "-cover.webp")
    if item.get("image_url") != default or not improved.is_file():
        return item
    return {
        **item,
        "image_url": BASE + "assets/editorial-illustrations/" + improved.name,
        "image_alt": "Original editorial illustration of " + str(item.get("title") or slug)
                     + ", not a photograph of a physically crocheted sample",
    }

def load_articles():
    """Published Supabase articles and intentional GitHub editorials only."""
    editorials = json.loads((ROOT / "content" / "github_articles.json").read_text(encoding="utf-8"))
    if not isinstance(editorials, list):
        raise RuntimeError("Expected GitHub editorial catalog array")
    url = API + "?status=eq.published&select=*&order=created_at.desc&limit=1000"
    req = Request(url, headers={"apikey": KEY, "Accept": "application/json", "User-Agent": "CozyLoopsStaticBuilder/1.0"})
    try:
        with urlopen(req, timeout=25) as response:
            remote = json.load(response)
        if not isinstance(remote, list):
            raise RuntimeError("Expected JSON list from Supabase")
    except (OSError, ValueError) as error:
        # Never republish a partial catalog: that would delete existing Supabase-only
        # pages from the generated manifest/sitemap when the REST API is briefly down.
        raise RuntimeError("Supabase article export unavailable; preserving the last published site") from error
    articles = {}
    # Supabase wins over GitHub editorial, so edits saved in Posts propagate.
    for item in editorials + remote:
        if (isinstance(item, dict) and isinstance(item.get("slug"), str)
                and item["slug"] not in REMOVED_STARTER_SLUGS
                and SLUG.fullmatch(item["slug"]) and isinstance(item.get("title"), str)
                and item["title"].strip() and item.get("status", "published") == "published"):
            # Preserve customized Admin uploads; upgrade only untouched originals.
            item = improved_editorial_cover(item)
            # The original GitHub editorial is sometimes mirrored in Supabase.
            # Upgrade only its unchanged legacy cover, never a custom Admin image.
            legacy = BASE + "assets/" + item["slug"] + "-1.webp"
            polished = ROOT / "assets" / "legacy-polished" / (item["slug"] + "-cover.webp")
            if item.get("image_url") == legacy and polished.is_file():
                item = {**item, "image_url": BASE + "assets/legacy-polished/" + polished.name}
            articles[item["slug"]] = item
    return sorted(articles.values(), key=lambda p: p.get("published_at") or p.get("created_at") or "", reverse=True)

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


EDITORIAL_NOTE = re.compile(r"(?m)^\*\*Editorial note:\*\* .*?(?=\n\s*\n|\Z)", re.S)

def normalize_article_content(source):
    """Move a long AI-visual disclosure out of the opening flow without hiding it.
    Keeps underlying instructions, cautions and all project-specific stitch counts.
    """
    content = str(source or "").strip()
    match = EDITORIAL_NOTE.search(content)
    if not match:
        return content, ""
    note = match.group(0).strip()
    clean = (content[:match.start()] + content[match.end():]).strip()
    # These repeated template paragraphs added no project-specific stitch guidance.
    # Keep each original pattern, safety warning, measurements, and FAQ answers.
    repeated_padding = (
        "Think of this as a small, useful project rather than a decorative photograph. Read the whole pattern before you cut yarn, then identify the edges, openings and pieces to sew before starting.",
        "For a reliable result, choose smooth yarn with visible stitches, the hook recommended by your yarn or pattern notes, a tapestry needle for secure finishing, and a stitch marker for shaping rounds. Avoid changing yarn weight halfway through the project: dimensions and texture can shift noticeably.",
        "Take a moment to stop at the end of each numbered row or round, count the top V-shaped stitches, and move your marker. It is faster to correct one row now than unravel several rows later.",
        "The most repeatable way to customize a crochet pattern is to change **one variable at a time**: yarn thickness, hook size, or the number of rows and rounds. Record any change and make a sample rather than promising a universal finished size.",
        "The most important part of learning crochet is producing something you can inspect and improve. Try the first version slowly, count each row, keep notes on your yarn and hook, and adapt the next version using what you learned.",
    )
    for filler in repeated_padding:
        clean = clean.replace(filler, "")
    photo_faq = re.compile(
        r"(?m)^### Why do the photos not match every stitch\?\n\n"
        r"All project images are AI-generated editorial visuals, not documentary step-by-step photos of a tested sample\. "
        r"The written stitch counts and assembly notes are the intended reference\. "
        r"If a technique or measurement is unclear, make a small swatch before continuing\."
    )
    clean = photo_faq.sub("", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
    return clean, note

def concise_editorial_illustrations(content):
    """Retain useful concept panels and avoid eight near-duplicate screenshots.
    The full unmodified source remains in Supabase/the editorial catalog.
    """
    blocks = re.split(r"(\n\s*\n)", content)
    kept = []
    for block in blocks:
        match = re.fullmatch(r"!\[[^\]]*\]\(https://cozyloops\.site/assets/[a-z0-9-]+-(\d\d)\.webp\)", block.strip())
        if match and match.group(1) not in ("02", "04", "09"):
            continue
        kept.append(block)
    return "".join(kept).strip()

def seo_description(article):
    """Unique, descriptive, concise snippet; avoid cutting a word in half."""
    source = re.sub(r"\s+", " ", str(article.get("excerpt") or "").strip())
    if not source:
        source = str(article.get("content") or "").split("\n", 1)[0]
    source = re.sub(r"\*\*", "", source).strip()
    if len(source) <= 160:
        return source
    return source[:158].rsplit(" ", 1)[0].rstrip(".,;:") + "…"

def render_page(article, css, articles=None):
    slug = article["slug"]
    title = str(article["title"])
    description = seo_description(article)
    canonical = BASE + "posts/" + quote(slug) + "/"
    cover = safe_image(article.get("image_url"))
    category = str(article.get("category") or "Crochet Patterns")
    related_html = render_related(article, articles or [])
    article_content, visual_note = normalize_article_content(article.get("content") or "")
    if visual_note:
        article_content = concise_editorial_illustrations(article_content)
    toc_html = table_of_contents(article_content)
    published = str(article.get("published_at") or article.get("created_at") or "")
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
    if article_content:
        structured["wordCount"] = len(article_content.split())
    is_starfish = article.get("slug") == "starfish-baby-crochet-outfit-guide"
    cover_width, cover_height = (720, 1257) if is_starfish else image_size(cover)
    article_class = "article starfish-featured" if is_starfish else "article"
    cover_alt = str(article.get("image_alt") or title)
    # The 2026 editorial collection uses concept images, not verified stitch photos.
    image_disclosure = '<figcaption>Illustrative crochet concept — follow the written stitch instructions.</figcaption>' if visual_note else ''
    is_illustration = "/assets/editorial-illustrations/" in cover
    hero_variant = " illustration-hero" if is_illustration else (" concept-hero" if visual_note else "")
    image_html = (f'<figure class="article-hero{hero_variant}"><img class="article-cover" src="{esc(cover)}" '
                  f'alt="{esc(cover_alt)}" width="{cover_width}" height="{cover_height}" '
                  f'fetchpriority="high" decoding="async">{image_disclosure}</figure>') if cover else ""
    structured_json = json.dumps(structured, ensure_ascii=False).replace("<", "\\u003c")
    social_image = f'<meta property="og:image" content="{esc(cover)}">' if cover else ""
    return inject_hb_ads(f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<script defer fetchpriority="low" src="https://d3u598arehftfk.cloudfront.net/prebid_hb_40300_44798.js"></script>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | CozyLoops</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{esc(canonical)}">
<link rel="icon" type="image/svg+xml" href="{BASE}favicon.svg">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:site_name" content="CozyLoops">
<meta property="og:locale" content="en_US">
{social_image}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<script type="application/ld+json">{structured_json}</script>
<script defer src="{BASE}scripts/article_analytics.js"></script>
<script defer src="../../scripts/site_navigation.js"></script>
<style>{css}

.article-cover{{max-height:520px;width:100%;height:auto;aspect-ratio:auto;object-fit:contain;border-radius:16px;background:#f8f5ef}}
.article-hero{{margin:22px 0 24px}}.article-hero img{{display:block;margin:0 auto}}
.article-hero figcaption{{font:12px/1.6 system-ui,sans-serif;text-align:center;color:#536153;margin:7px auto 0}}
.illustration-hero{{display:flex;flex-direction:column;align-items:center}}
.illustration-hero .article-cover{{width:100%;height:auto;max-width:860px;max-height:none;aspect-ratio:8/5;object-fit:contain;background:#f9f6ef;box-shadow:0 10px 28px #2b352b0b}}
.concept-hero{{display:flex;flex-direction:column;align-items:center}}
.concept-hero .article-cover{{width:min(100%,340px);height:340px;aspect-ratio:1;object-fit:cover;object-position:left center;max-height:340px;box-shadow:0 10px 28px #2b352b12}}
@media(max-width:640px){{.concept-hero .article-cover{{width:min(100%,310px);height:min(82vw,310px)}}}}
.article figure:not(.article-hero) img{{max-width:min(100%,650px);display:block;margin:0 auto}}
.article figure:not(.article-hero){{margin:24px 0}}
.article-toc{{margin:16px 0 28px;padding:0 18px;background:#fff;border:1px solid #e3e8df;border-radius:14px}}
.article-toc summary{{padding:15px 4px;cursor:pointer;font:700 14px/1.5 system-ui,sans-serif;color:#294332;min-height:44px}}
.article-toc nav{{border-top:1px solid #e3e8df;padding:10px 0 15px;max-height:285px;overflow-y:auto}}
.article-toc ol{{margin:4px 0;padding-left:22px}}.article-toc li{{margin:4px 0}}
.article-toc a{{display:inline-flex;align-items:center;min-height:36px;color:#24432d;text-underline-offset:3px}}
.article-disclosure{{margin:38px 0 12px;padding:0 18px;border:1px solid #e4e8e2;border-radius:14px;background:#fafbf8}}
.article-disclosure summary{{cursor:pointer;padding:15px 2px;min-height:48px;font-weight:650}}
.article-disclosure p{{font-size:14px;line-height:1.7;color:#35463b}}
.article>h1{{line-height:1.12;text-wrap:balance;overflow-wrap:break-word}}
@media(max-width:640px){{.article>h1{{font-size:clamp(30px,7.2vw,42px);line-height:1.13;letter-spacing:-.015em}}.article-hero{{margin:16px 0 20px}}.article-toc{{margin-bottom:20px}}.article-share{{gap:8px}}}}

.starfish-featured .article-cover{{width:min(100%,640px);max-height:none;height:auto;aspect-ratio:auto;object-fit:contain;margin:24px auto 34px;box-shadow:0 12px 40px #29342d0d}}
.starfish-featured figure img{{max-width:670px;margin:16px auto;object-fit:contain}}
.article figure{{margin:22px 0}}.article figure img{{width:100%;height:auto;border-radius:15px}}
.article ul{{padding-left:26px}}.article strong{{font-weight:700}}
.related-posts{{margin:32px 0;padding:22px;border:1px solid var(--line,#e5e7df);border-radius:16px;background:var(--white,#fff)}}
.article h2[id],.article h3[id],.article h4[id]{{scroll-margin-top:24px}}
.related-posts ul{{margin:12px 0 0;padding-left:22px}}.related-posts li{{margin:8px 0}}.related-posts a{{text-decoration:underline;text-underline-offset:3px}}
.article-share{{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:10px 0 24px}}.article-share-button{{min-height:44px;border:1px solid var(--green,#4f694c);background:transparent;color:var(--green,#4f694c);border-radius:25px;padding:8px 16px;font:600 14px/1.4 system-ui,sans-serif;cursor:pointer}}.article-share-button:hover,.article-share-button:focus-visible{{background:var(--green,#4f694c);color:white}}#article-share-status{{font-size:14px;color:var(--muted,#68736a)}}
.article-print-button{{min-height:44px;border:1px solid var(--line,#e5e7df);background:var(--white,#fff);color:var(--ink,#29342d);border-radius:25px;padding:8px 16px;font:600 14px/1.4 system-ui,sans-serif;cursor:pointer}}.article-print-button:hover,.article-print-button:focus-visible{{border-color:var(--green,#4f694c);color:var(--green,#4f694c)}}
@media print{{@page{{margin:16mm}}html,body{{background:white!important;color:#111!important;font:11pt/1.45 Georgia,serif!important}}header,footer,.back,.article-share,.article-toc,.related-posts,.article-privacy,.privacy-choice,.skip-link{{display:none!important}}main#content{{display:block!important;padding:0!important;margin:0!important}}.article{{max-width:none!important;width:100%!important;margin:0!important;padding:0!important;box-shadow:none!important;border:0!important;background:white!important}}.article-cover{{display:none!important}}.article h1{{font-size:24pt!important;margin:0 0 12pt!important}}.article h2{{font-size:16pt!important}}.article h3{{font-size:13pt!important}}.article h2,.article h3,.article h4{{break-after:avoid}}.article p,.article li{{orphans:3;widows:3}}.article figure img{{max-width:100%!important;height:auto!important;break-inside:avoid}}.article a{{color:#111!important;text-decoration:none!important}}.article>.btn{{display:none!important}}}}
.reading-progress{{position:fixed;top:0;left:0;right:0;height:4px;background:transparent;z-index:9999;pointer-events:none}}.reading-progress span{{display:block;height:100%;width:0;background:var(--green,#4f694c);transition:width .12s linear}}@media print{{.reading-progress{{display:none!important}}}}@media(prefers-reduced-motion:reduce){{.reading-progress span{{transition:none}}}}
.back-to-top{{position:fixed;z-index:65;right:18px;bottom:20px;padding:12px 17px;border:1px solid var(--line,#e5e7df);border-radius:999px;box-shadow:0 4px 18px #29342d22;background:var(--white,#fff);color:var(--green,#4f694c);font:700 14px system-ui,sans-serif;cursor:pointer}}.back-to-top:hover,.back-to-top:focus-visible{{background:var(--green,#4f694c);color:#fff}}.back-to-top[hidden]{{display:none!important}}@media print{{.back-to-top{{display:none!important}}}}@media(max-width:600px){{.back-to-top{{bottom:12px;right:12px}}}}
</style>
</head>
<body>
<a class="skip-link" href="#content">Skip to content</a>
<header><nav class="nav top-nav" aria-label="Main navigation"><a class="brand" href="{BASE}">CozyLoops ♡</a><div class="top-links" aria-label="Site pages"><a href="{BASE}#home">Home</a><a href="{BASE}#articles">Articles</a><a href="{BASE}#categories">Categories</a><a href="{BASE}#about">About</a><a href="{BASE}#contact">Contact</a></div><a class="nav-search-trigger" href="{BASE}#search-articles" aria-label="Search crochet articles" title="Search articles"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><circle cx="10.8" cy="10.8" r="6.8"></circle><path d="m16 16 5 5"></path></svg></a></nav></header>
<div class="reading-progress" id="reading-progress" role="progressbar" aria-label="Article reading progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><span></span></div>
<button type="button" id="back-to-top" class="back-to-top" aria-label="Back to top" hidden>↑ Top</button>
<main id="content"><article class="{article_class}">
<a class="back" href="{BASE}#articles">← Back to all articles</a>
<div class="tag">{esc(category)}</div>
<h1>{esc(title)}</h1>
<p class="meta">By CozyLoops</p>
<div class="article-share"><button type="button" id="article-share-button" class="article-share-button">Share this article</button><button type="button" id="article-print-button" class="article-print-button">Print / Save PDF</button><span id="article-share-status" role="status" aria-live="polite"></span></div>
<p>{esc(description)}</p>
{image_html}
{toc_html}
{markdown(article_content)}
{('<details class="article-disclosure"><summary>About this guide and its illustrations</summary><p>' + linked_text(visual_note) + '</p></details>') if visual_note else ''}
{related_html}
<h2>Keep Creating</h2>
<p>Explore more crochet articles and patterns at CozyLoops.</p>
<a class="btn" href="{BASE}#articles">Browse all articles</a>
<section class="article-privacy" aria-label="Analytics preferences"><h2>Analytics preferences</h2><p id="article-consent-status" role="status">You can disable optional analytics for this browser at any time.</p><button type="button" id="article-privacy-opt-out" class="btn">Disable optional analytics</button></section>
</article></main>
<aside id="privacy-choice" class="privacy-choice" aria-label="Optional article analytics" hidden><strong>Help us improve CozyLoops?</strong><p>With your permission, we count this article view once per browser per day. We store no names, emails or IP addresses in our analytics table. You can decline and keep reading.</p><div class="actions"><button type="button" id="privacy-decline">No thanks</button><button type="button" class="accept" id="privacy-accept">Allow analytics</button></div></aside>
<footer><div class="footer-inner"><div><a class="brand" href="{BASE}">CozyLoops ♡</a><p>Slow down, pick up your yarn, and create something lovely.</p></div><div><a href="{BASE}#about">About</a><a href="{BASE}#contact">Contact</a><a href="{BASE}#privacy">Privacy</a></div></div></footer>
</body></html>
''')

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
    from security_policy import main as apply_security_policy
    apply_security_policy()
    print(f"Generated {len(current)} SEO article pages and sitemap entries")

if __name__ == "__main__":
    main()
