#!/usr/bin/env python3
"""Poll Frantic seals (Oath + Lantern) after GitHub actions."""
import json
import urllib.request
import urllib.error

with open("/home/mihai/secrets/frantic_agent.json") as f:
    d = json.load(f)

kid = d["agent_slug"]
token = d["agent_token"]
req = urllib.request.Request(
    f"https://gofrantic.com/v1/agents/{kid}/seals",
    data=json.dumps({}).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}",
             "User-Agent": "vasilica-agent/0.1"},
    method="POST")
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode()[:500])
    raise SystemExit

# persist updated state
with open("/home/mihai/secrets/frantic_agent.json", "w") as f:
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
v = red.get("verification", {})
seals = v.get("seals", {})
print("sealed_count:", v.get("sealed_count"), "| sworn:", v.get("sworn"))
for name, s in seals.items():
    print(f"  {name}: {s.get('state')}")
print(json.dumps({k: red[k] for k in red if k in ("runway", "eligible", "eligibility_reason")}, indent=1))