#!/usr/bin/env python3
"""Read-only production HTTP security header audit. Never treats HTML meta CSP as a header.

GitHub Pages does not support custom response security headers. Print actionable
missing protections without turning this availability check into a false claim.
"""
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from datetime import datetime, timezone

BASE="https://cozyloops.site"
PAGES=("/", "/admin/", "/contact/", "/contact/thanks/", "/posts/crochet-tulip-bouquet-stems-guide/")
REQUIRED={
    "strict-transport-security":"HSTS: configure at Cloudflare edge / HTTPS proxy",
    "content-security-policy":"HTTP CSP: needed for frame-ancestors enforcement; META CSP is insufficient",
    "x-content-type-options":"nosniff: response header must be set by the edge",
    "referrer-policy":"Restrict cross-origin referrer metadata",
    "permissions-policy":"Disable unused camera, microphone, geolocation capabilities",
    "x-frame-options":"Protect against embedding (or provide equivalent frame-ancestors CSP)",
}
RESULT=Path("security/live-header-audit.json")

def main():
    report={"audited_at":datetime.now(timezone.utc).isoformat(),"host":urlsplit(BASE).hostname,"pages":[]}
    critical=[]
    for path in PAGES:
        url=BASE+path
        with urlopen(Request(url,headers={"User-Agent":"CozyLoops-HeaderAudit/1.0"}),timeout=25) as res:
            final=res.geturl()
            if urlsplit(final).hostname!=urlsplit(BASE).hostname:
                raise RuntimeError("Unexpected redirect origin: "+final)
            headers={k.lower():v for k,v in res.headers.items()}
            if res.status!=200:
                raise RuntimeError(f"Failed to inspect {url}: HTTP {res.status}")
        missing={k:reason for k,reason in REQUIRED.items() if not headers.get(k)}
        policy=headers.get("content-security-policy","")
        if path=="/contact/" and policy:
            # Real FormSubmit POST would fail behind a global form-action 'self' CSP.
            actions=next((part.strip() for part in policy.split(";")
                          if part.strip().startswith("form-action ")), "")
            if actions and "https://formsubmit.co" not in actions and "*" not in actions:
                critical.append("Contact CSP prohibits the live FormSubmit endpoint: "+actions)
        if path=="/contact/thanks/":
            report["confirmation_noindex_header"]=headers.get("x-robots-tag","")
        page={"path":path, "present":{k:headers[k] for k in REQUIRED if k in headers}, "missing":missing}
        report["pages"].append(page)
        print(f"{path}: {len(REQUIRED)-len(missing)} of {len(REQUIRED)} response headers present")
        for key,reason in missing.items():
            print(f"  ::warning title=Missing production security header::{key} — {reason}")
    RESULT.parent.mkdir(parents=True,exist_ok=True)
    RESULT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("This is an observed header inventory, NOT a vulnerability exploit scan.")
    print("Raw report:",RESULT)
    for problem in critical:
        print("::error title=Broken Contact security policy::"+problem)
    return 1 if critical else 0

if __name__=="__main__":
    raise SystemExit(main())
