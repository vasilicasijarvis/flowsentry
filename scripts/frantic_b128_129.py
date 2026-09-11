#!/usr/bin/env python3
"""Read Frantic bounty 128 + 129 full descriptions."""
import json
import urllib.request

for num in ("128", "129"):
    req = urllib.request.Request(f"https://gofrantic.com/v1/bounties/{num}",
                                 headers={"User-Agent": "vasilica-agent/0.1"})
    d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
    b = d["bounty"]
    print(f"===== #{num} ${b.get('price_usd')}")
    print(b["description"])
    print()