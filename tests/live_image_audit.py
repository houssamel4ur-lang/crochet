#!/usr/bin/env python3
"""Read-only audit of images embedded in the deployed CozyLoops articles.

Checks HTTPS article covers and inline images by sending HEAD. No content
is downloaded or stored. Third-party providers can rate-limit requests;
a transient network error is reported separately rather than hidden.
"""
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import ssl
import sys
import time

BASE = "https://houssamel4ur-lang.github.io/crochet/"
class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images=[]
    def handle_starttag(self,tag,attrs):
        if tag == 'img':
            a=dict(attrs)
            if a.get('src'):
                self.images.append((a['src'],a.get('alt','')))

def fetch(url):
    with urlopen(Request(url, headers={"User-Agent":"CozyLoopsAssetAudit/1.0"}),timeout=20) as r:
        return r.read().decode('utf-8')

def image_status(url):
    req=Request(url,method="HEAD",headers={"User-Agent":"Mozilla/5.0 CozyLoopsAssetAudit/1.0"})
    try:
        with urlopen(req,timeout=20) as response:
            return response.status,response.headers.get('Content-Type',''),''
    except HTTPError as e:
        return e.code,'',str(e)
    except (TimeoutError, URLError, ssl.SSLError) as e:
        return None,'',str(e)

def main():
    manifest=json.loads(fetch(BASE+'posts/manifest.json'))
    if not manifest:
        raise RuntimeError('No live articles found')
    sources={}
    for slug in manifest:
        html=fetch(BASE+'posts/'+slug+'/')
        parser=ImageParser()
        parser.feed(html)
        for url,alt in parser.images:
            full=urljoin(BASE+'posts/'+slug+'/',url)
            sources.setdefault(full,[]).append((slug,alt))
    failures=[]
    skipped=[]
    for url,used in sources.items():
        print('Checking image:',url.split('?')[0], 'articles:', ','.join(slug for slug,_ in used))
        parts=urlsplit(url)
        if parts.scheme!='https':
            failures.append((url,'Non-HTTPS image URL'))
            continue
        if not all(alt.strip() for _,alt in used):
            failures.append((url,'Image lacks alt text'))
        status,kind,error=image_status(url)
        if status in (200,206) and kind.lower().startswith('image/'):
            print('  OK:',status,kind)
        elif status in (429,500,502,503,504) or status is None:
            skipped.append((url,status,error or kind))
            print('  TRANSIENT:',status,error or kind)
        else:
            failures.append((url,'HTTP '+str(status)+' / '+(kind or error)))
            print('  BROKEN:',status,kind or error)
    print('Image URLs:',len(sources),'broken:',len(failures),'transient:',len(skipped))
    for url,problem in failures:
        print('FAIL:',problem,url)
    for url,status,problem in skipped:
        print('WARN: uncertain reachability:',status,problem,url)
    # No false green: fail on clearly broken images. Transients remain warnings.
    return 1 if failures else 0

if __name__ == '__main__':
    sys.exit(main())
