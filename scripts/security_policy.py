"""Apply the security controls supported by static GitHub Pages hosting.

Admin inline code is authorized by its exact SHA-256, never unsafe-inline.
Public ad scripts retain their existing behavior; no claim of XSS isolation there.
"""
import base64
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = re.compile(r'\n?<!-- cozy-security:start -->.*?<!-- cozy-security:end -->\n?', re.S)

def protect(source, admin=False, external_contact_form=False):
    source = MARKER.sub('', source)
    form_destinations = "form-action 'self' https://formsubmit.co" if external_contact_form else "form-action 'self'"
    policy = "base-uri 'none'; object-src 'none'; " + form_destinations + "; upgrade-insecure-requests"
    if admin:
        hashes = []
        for attrs, body in re.findall(r'<script\b([^>]*)>(.*?)</script>', source, re.S | re.I):
            if not re.search(r'\bsrc\s*=', attrs, re.I):
                digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
                hashes.append("'sha256-" + digest + "'")
        policy = ("default-src 'none'; base-uri 'none'; object-src 'none'; form-action 'self'; "
                  "script-src 'self' https://esm.sh https://cdn.jsdelivr.net " + ' '.join(hashes) + "; "
                  "style-src 'self' 'unsafe-inline'; img-src 'self' https: blob: data:; "
                  "connect-src 'self' https://yqmrunstyhrhnvxoyrap.supabase.co; "
                  "frame-src 'none'; worker-src 'none'; manifest-src 'none'; upgrade-insecure-requests")
    block = ('\n<!-- cozy-security:start -->\n'
             '<meta http-equiv="Content-Security-Policy" content="' + policy + '">\n'
             '<meta name="referrer" content="strict-origin-when-cross-origin">\n'
             '<!-- cozy-security:end -->\n')
    # CSP must precede all scripts and resource loads, immediately after charset.
    return re.sub(r'(<meta charset="utf-8"\s*/?>)', lambda m: m.group(1) + block, source, count=1, flags=re.I)

def main():
    legal_slugs = ('about', 'contact', 'privacy-policy', 'terms', 'disclosure', 'cookie-policy', 'sitemap')
    legal_paths = [ROOT / slug / 'index.html' for slug in legal_slugs if (ROOT / slug / 'index.html').is_file()]
    receipt_page = ROOT / 'contact' / 'thanks' / 'index.html'
    if receipt_page.is_file():
        legal_paths.append(receipt_page)
    paths = [ROOT / 'index.html', ROOT / 'admin/index.html', ROOT / '404.html', *sorted((ROOT / 'posts').glob('*/index.html')), *legal_paths]
    for path in paths:
        text = path.read_text()
        path.write_text(protect(text, path.parent.name == 'admin', path.parent.name == 'contact'))
    print(f'Applied static security policy to {len(paths)} pages')

if __name__ == '__main__':
    main()
