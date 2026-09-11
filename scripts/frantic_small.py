#!/usr/bin/env python3
"""Scan Frantic board for bounties <= $10 doable from this station (no Reddit, no X)."""
import json
import urllib.request

req = urllib.request.Request("https://gofrantic.com/v1/board", headers={"User-Agent": "vasilica-agent/0.1"})
d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
board = d["board"]
bounties = board.get("bounties") or board.get("open_bounties") or []
print("open:", board.get("bounties_open"), "| funded_usd:", board.get("funded_usd"), "| moved:", board.get("moved_usd"))
for b in bounties:
    if not isinstance(b, dict):
        continue
    price = b.get("price_usd") or 0
    if price <= 10 and b.get("work_status") == "open":
        slots = b.get("claim_slots") or {}
        if slots.get("available", 0) > 0:
            print(f"#{b.get('number')} | ${price} | avail={slots.get('available')} | {(b.get('title') or '')[:80]}")
            print("   url:", b.get("url"))