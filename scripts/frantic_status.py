#!/usr/bin/env python3
"""Frantic agent status: eligibility, runway, work queue."""
import json
import urllib.request
import urllib.error

with open("/home/mihai/secrets/frantic_agent.json") as f:
    d = json.load(f)
kid = d.get("agent_slug") or (d.get("verification", {}) or {}).get("agent_kid") or "agent-a3ea73"
token = d.get("agent_token")

req = urllib.request.Request(
    f"https://gofrantic.com/v1/agents/{kid}/status",
    headers={"Authorization": f"Bearer {token}", "User-Agent": "vasilica-agent/0.1"})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode()[:600])
    raise SystemExit

with open("/home/mihai/secrets/frantic_agent_status.json", "w") as f:
    json.dump(out, f, indent=1)

red = json.loads(json.dumps(out))
def scrub(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if "token" in k.lower() and isinstance(v, str) and len(v) > 8:
                o[k] = v[:6] + "..."
            else:
                scrub(v)
    elif isinstance(o, list):
        for x in o:
            scrub(x)
scrub(red)
a = red.get("agent", red)
print("lifecycle:", a.get("lifecycle") or a.get("state"))
print("runway:", json.dumps(a.get("runway", {}))[:200])
print("claimEligibility:", json.dumps(a.get("claimEligibility", {}))[:400])
print("standing:", json.dumps(a.get("standing", {}))[:200])
work = a.get("work", {})
print("work items:", len((work.get("items") or [])))