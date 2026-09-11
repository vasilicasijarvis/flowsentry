#!/usr/bin/env python3
"""Check x402.org facilitator discovery + x402-list + x402discovery catalogs for flowsentry."""
import json
import urllib.request

CHECKS = [
    ("x402.org facilitator", "https://www.x402.org/facilitator/discovery/resources"),
    ("x402-list services", "https://x402-list.com/api/v1/services?status=online"),
    ("x402discovery catalog", "https://x402-discovery-api.onrender.com/catalog"),
]


def find(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        body = urllib.request.urlopen(req, timeout=45).read().decode()
        low = body.lower()
        n = body.count('"resource"') or len(low)
        hits = [seg for seg in ("flowsentry", "flow-sentry") if seg in low]
        print(f"{url} -> len={len(body)} flowsentry_hits={hits}")
        if hits:
            i = low.find("flowsentry")
            print("   ctx:", body[max(0, i - 200):i + 300].replace("\n", " ")[:480])
    except Exception as e:
        print(f"{url} -> ERR {str(e)[:100]}")


for name, url in CHECKS:
    print("==", name)
    find(url)