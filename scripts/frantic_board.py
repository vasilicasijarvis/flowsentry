#!/usr/bin/env python3
"""Frantic bounty board snapshot (open, funded, claimable)."""
import json
import urllib.request

req = urllib.request.Request("https://gofrantic.com/v1/board",
                             headers={"User-Agent": "vasilica-agent/0.1"})
d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
board = d.get("board", {})
bounties = board.get("open_bounties") or board.get("bounties") or []
print("keys:", list(d.keys())[:12], "| board keys:", list(board.keys())[:14])
print("bounties:", len(bounties))
for b in bounties[:30]:
    if isinstance(b, dict):
        print(f"#{b.get('number')} | ${b.get('price_usd')} | {b.get('work_status')} | "
              f"slots={b.get('claim_slots')} | {(b.get('title') or '')[:70]}")