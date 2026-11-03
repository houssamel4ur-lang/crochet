#!/usr/bin/env python3
"""Non-destructive checks against the public Supabase REST API.

Uses only the public publishable key and never writes or deletes data.
This tests observable anonymous access, not the complete set of RLS policies.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import unittest

BASE = "https://yqmrunstyhrhnvxoyrap.supabase.co/rest/v1/"
PUBLIC_KEY = "sb_publishable_HqkcpvBz8P8KJTZFgefrWQ_rFxKPMNh"

def request(path, query=None, method="GET", payload=None):
    url = BASE + path
    if query is not None:
        url += "?" + urlencode(query)
    headers = {"apikey": PUBLIC_KEY, "Accept": "application/json", "User-Agent": "CozyLoopsSecurityCheck/1.0"}
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, headers=headers, data=body, method=method)
    try:
        with urlopen(req, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as err:
        response_body = err.read(2048).decode("utf-8", errors="replace")
        try:
            response_body = json.loads(response_body)
        except ValueError:
            pass
        return err.code, response_body

class AnonymousPermissions(unittest.TestCase):
    def test_public_articles_only_published(self):
        code, data = request("articles", {"select": "slug,status", "limit": "50"})
        self.assertEqual(code, 200, "Published posts should be publicly readable")
        self.assertIsInstance(data, list)
        self.assertTrue(all(post.get("status") == "published" for post in data),
                        "Anonymous query exposed non-published articles")

    def test_drafts_cannot_be_read_by_anonymous_users(self):
        code, data = request("articles", {"select": "slug,status", "status": "eq.draft", "limit": "5"})
        self.assertTrue(code in (200, 401, 403, 404), "Unexpected response checking draft visibility")
        if code == 200:
            self.assertEqual(data, [], "DRAFT CONTENT EXPOSED TO ANONYMOUS USERS")

    def test_hidden_social_links_are_not_exposed(self):
        code, data = request("social_links", {"select": "platform,is_visible", "is_visible": "eq.false", "limit": "10"})
        self.assertIn(code, (200, 401, 403, 404))
        if code == 200:
            self.assertEqual(len(data), 0, "Anonymous query exposed hidden contact/social links")

    def test_public_theme_is_readable(self):
        code, data = request("site_settings", {"select": "site_name,site_description", "id": "eq.1", "limit": "1"})
        self.assertEqual(code, 200, "Public homepage needs to read site title and description")
        self.assertIsInstance(data, list)

    def test_private_view_rows_are_not_exposed(self):
        code, data = request("page_views", {"select": "visitor_hash,page_key", "limit": "1"})
        self.assertTrue(code in (401, 403, 404) or (code == 200 and data == []),
                        "Anonymous users can access analytics database rows")
        if code == 200:
            self.assertEqual(data, [])

    def test_analytics_rpc_denies_anonymous_users(self):
        # RPC computes a summary; the request never inserts/updates/deletes anything.
        code, data = request("rpc/cozyloop_analytics", method="POST", payload={})
        self.assertNotEqual(code, 200, "Admin analytics summary exposed to anonymous users")

    def test_super_admin_rpc_does_not_grant_anonymous_access(self):
        code, data = request("rpc/is_super_admin", method="POST", payload={})
        self.assertFalse(code == 200 and data is True, "Anonymous user mistakenly gets super_admin")

if __name__ == "__main__":
    unittest.main(verbosity=2)
