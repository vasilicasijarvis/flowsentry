#!/usr/bin/env python3
"""Scan Bazaar catalog pages for flowsentry (all pages, exact search)."""
import json
import urllib.request

BASE = "https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources"


def fetch(q, page=0):
    url = f"{BASE}?q={q}&page={page}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())


if __name__ == "__main__":
    seen_total = 0
    hits = []
    for page in range(8):
        try:
            d = fetch("flowsentry", page)
        except Exception as e:
            print(f"page {page}: ERR {str(e)[:60]}")
            break
        items = d.get("items", [])
        if not items:
            break
        seen_total += len(items)
        for it in items:
            if "flowsentry" in json.dumps(it).lower():
                hits.append(it.get("resource"))
    print("scanned:", seen_total, "hits:", len(hits))
    for h in hits:
        print("  HIT:", h)