#!/usr/bin/env python3
"""Offline security regression tests for the static SEO article renderer."""
import unittest
from html.parser import HTMLParser
from scripts.build_seo import safe_image, markdown, render_page, BASE

class DangerousAttributes(HTMLParser):
    def __init__(self):
        super().__init__()
        self.events=[]
        self.urls=[]
    def handle_starttag(self,tag,attrs):
        data=dict(attrs)
        self.events.extend(key for key in data if key.startswith('on'))
        if tag=='img':
            self.urls.append(data.get('src',''))

class StaticArticleSecurityTests(unittest.TestCase):
    def test_reject_unsafe_image_urls(self):
        invalid = [
            'javascript:alert(1)', 'data:image/svg+xml,<svg>',
            'http://example.com/pic.jpg', 'https:///pic.jpg',
            'https://', 'https://user:pass@example.com/a.jpg',
            'https://example.com/abc" onerror="alert(1)',
            'https://example.com/\\nattack.jpg',
            'https://example.com/a b.jpg',
            'https://example.com:8080/asset.jpg',
            'https://example.com/\\\\evil'
        ]
        for url in invalid:
            with self.subTest(url=url):
                self.assertEqual(safe_image(url), '')
        self.assertEqual(safe_image('https://images.example.org/photo.jpg?w=300&crop=1'),
                         'https://images.example.org/photo.jpg?w=300&crop=1')

    def test_markdown_renders_user_html_as_text(self):
        result=markdown('## <img src=x onerror=alert(1)>\\n\\n**<script>alert(1)</script>**\\n\\n'
                        '![\" onerror=\"alert(1)](https://example.com/test.png)')
        self.assertNotIn('<script>',result)
        self.assertNotIn('<img src=x',result)
        scan=DangerousAttributes()
        scan.feed(result)
        self.assertEqual(scan.events,[])
        self.assertIn('https://example.com/test.png',scan.urls)

    def test_page_metadata_and_cover_are_escaped(self):
        article={
            'slug':'security-test',
            'title':'Crochet \"/><script>alert(1)</script>',
            'excerpt':'A careful introduction <img src=x onerror=alert(1)>',
            'content':'## <img src=x onerror=alert(1)>',
            'category':'Free Patterns <script>alert(2)</script>',
            'created_at':'2026-11-03T10:00:00+00:00',
            'image_url':'https://example.org/picture.jpg\" onload=\"alert(1)'
        }
        result=render_page(article,'body{color:black}')
        self.assertNotIn('<script>alert(1)</script>',result)
        # Event-handler words in escaped article text are harmless; check parsed attributes instead.
        scan=DangerousAttributes()
        scan.feed(result)
        self.assertEqual(scan.events,[])
        self.assertNotIn('https://example.org/picture.jpg',scan.urls)
        self.assertIn(BASE+'posts/security-test/',result)

if __name__=='__main__':
    unittest.main(verbosity=2)
