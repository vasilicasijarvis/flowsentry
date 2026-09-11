#!/usr/bin/env python3
"""Find x402-paid AI/security services on Bazaar to target for outreach + partnerships."""
import json
import urllib.request

BASE = "https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources"


def fetch(page=0):
    url = f"{BASE}?page={page}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())


def main():
    seen = {}
    for page in range(5):
        try:
            d = fetch(page)
        except Exception as e:
            print("page", page, "ERR", str(e)[:60])
            break
        items = d.get("items", [])
        if not items:
            break
        for it in items:
            r = it.get("resource", "")
            if r in seen:
                continue
            seen[r] = it
    # candidates: vercel.app endpoints (small sellers, likely responsive agents)
    print("== vercel.app endpoints ==")
    for r, it in sorted(seen.items()):
        if "vercel.app" in r:
            acc = (it.get("accepts") or [{}])[0]
            md = it.get("metadata") or {}
            prov = (md.get("provider") or {})
            print("-", r, "|", acc.get("amount"), "USDC units |", (prov.get("name") or "")[:30])
    print("total scanned:", len(seen))


if __name__ == "__main__":
    main()