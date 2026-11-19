import base64
import hashlib
from pathlib import Path
import re
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from security_policy import protect, ROOT

class SecurityPolicy(unittest.TestCase):
    def test_admin_hash_matches_current_script(self):
        # The static admin is a single self-contained page: Supabase loads
        # from jsDelivr and the rest is inline scripts authorized by hash.
        source = (ROOT / 'admin/index.html').read_text()
        policy = re.search(r'Content-Security-Policy" content="([^"]+)', source)[1]
        script_src = policy.split('script-src ')[1].split(';')[0]
        self.assertNotIn("'unsafe-inline'", script_src)
        self.assertIn("https://cdn.jsdelivr.net", script_src)
        self.assertIn("connect-src 'self' https://yqmrunstyhrhnvxoyrap.supabase.co", policy)
        digests = 0
        for attrs, body in re.findall(r'<script\b([^>]*)>(.*?)</script>', source, re.S):
            if re.search(r'\bsrc\s*=', attrs):
                continue
            digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
            self.assertIn("'sha256-" + digest + "'", policy)
            digests += 1
        self.assertGreater(digests, 0, 'static admin inline scripts must be hashed into the policy')
        self.assertNotIn('<script type="module" src="./app.js"></script>', source)
        self.assertLess(source.index('Content-Security-Policy'), source.index('<script'))
        self.assertEqual(protect(source, True), source)

    def test_generated_pages_keep_policy(self):
        for path in (ROOT / 'posts').glob('*/index.html'):
            source = path.read_text()
            self.assertIn("base-uri 'none'; object-src 'none'; form-action 'self'", source)
