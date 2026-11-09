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
        source = (ROOT / 'admin/index.html').read_text()
        policy = re.search(r'Content-Security-Policy" content="([^"]+)', source)[1]
        self.assertNotIn("'unsafe-inline'", policy.split('script-src ')[1].split(';')[0])
        for body in re.findall(r'<script[^>]*>(.*?)</script>', source, re.S):
            digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
            self.assertIn("'sha256-" + digest + "'", policy)
        self.assertLess(source.index('Content-Security-Policy'), source.index('<script'))
        self.assertEqual(protect(source, True), source)

    def test_generated_pages_keep_policy(self):
        for path in (ROOT / 'posts').glob('*/index.html'):
            source = path.read_text()
            self.assertIn("base-uri 'none'; object-src 'none'; form-action 'self'", source)
