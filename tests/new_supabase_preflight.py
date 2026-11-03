#!/usr/bin/env python3
"""Read-only preflight before migrating CozyLoops to a different Supabase project."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://yqmrunstyhrhnvxoyrap.supabase.co/rest/v1/"
KEY = "sb_publishable_BpOaWu4aKoE5saOhdjaT-g_c9vTG3o8"

def get(table, params):
    url = BASE + table + "?" + urlencode(params)
    req = Request(url, headers={"apikey": KEY, "Accept": "application/json",
                                "User-Agent": "CozyLoops-Migration-Preflight/1.0"})
    try:
        with urlopen(req, timeout=20) as response:
            return json.load(response)
    except HTTPError as exc:
        details = exc.read(1024).decode("utf-8", errors="replace")
        raise AssertionError(f"{table}: HTTP {exc.code}: {details}; investigate schema, project, and RLS") from exc
    except URLError as exc:
        raise AssertionError(f"{table}: unreachable ({exc.reason})") from exc

def main():
    published = get("articles", {"status": "eq.published", "select": "slug,title,status", "limit": "1000"})
    assert isinstance(published, list), "articles query did not return a list"
    slugs = [row["slug"] for row in published if isinstance(row, dict) and row.get("slug")]
    assert slugs, "No publicly visible published articles; refusing production migration"
    settings = get("site_settings", {"id": "eq.1", "select": "site_name", "limit": "1"})
    assert isinstance(settings, list) and settings and settings[0].get("site_name"), "Missing public site settings"
    social = get("social_links", {"is_visible": "eq.true", "select": "platform", "limit": "20"})
    assert isinstance(social, list), "Public social_links query did not return a list"
    print("Public project preflight OK:", len(slugs), "published articles;", len(social), "visible social links")
    print("Published slugs:", ", ".join(sorted(slugs)))
    print("This check does not verify Admin write privileges, private data, or storage policies.")

if __name__ == "__main__":
    main()
