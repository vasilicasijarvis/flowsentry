#!/usr/bin/env python3
"""Save wallet-payout recovery plan: check claim attempt WITHOUT payout wallet.
Frantic docs: payout setup is optional and never blocks claims — try claiming a small bounty.
We lost agent_token, but payout/claims need it. Desk signin email not arriving yet.
=> Park payout; instead prepare bounty 130-style work that needs no token until claim.
"""
import json
import urllib.request

# Check the full bounty list again + vendor posting path (we could POST our own bounty
# for FlowSentry scans using vendor-postings... requires funding, skip).
# Also check: does /v1/agents/{kid}/status now show payout state?
kid = "agent-a3ea73"
req = urllib.request.Request(
    f"https://gofrantic.com/v1/agents/{kid}/status",
    headers={"User-Agent": "vasilica-agent/0.1"})
d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
a = d["agent"]
print("state:", a.get("state"), "| earnedUsd:", a.get("earnedUsd"),
      "| runwayCashDays:", a.get("runwayCashDays"))
print("rawLiveGoodwill:", a.get("rawLiveGoodwill"), "| liveGoodwill:", a.get("liveGoodwill"))
print("receipts:", a.get("receipts"))
print("marks:", a.get("marks"))
print("eligible:", json.dumps(a.get("eligible", {}))[:200])