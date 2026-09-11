#!/usr/bin/env python3
"""Inspect Frantic bounty 97 + 33 details (required artifacts, acceptance)."""
import json

for num in ("97", "33", "130", "128", "129"):
    import urllib.request
    req = urllib.request.Request(f"https://gofrantic.com/v1/bounties/{num}",
                                 headers={"User-Agent": "vasilica-agent/0.1"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
    except Exception as e:
        print(f"#{num}: ERR", str(e)[:60])
        continue
    b = d.get("bounty", {})
    print(f"===== #{num} {b.get('title', '')[:60]} | ${b.get('price_usd')}")
    desc = b.get("description") or ""
    print(desc[:900])
    print("  required_artifacts:", b.get("required_artifacts"))
    print()