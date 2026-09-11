#!/usr/bin/env python3
"""Final 2h-cycle sweep + RAPORT 2H #10 appendix before session wrap."""
import json
import subprocess
import urllib.request

lines = []

# inbox
r = subprocess.run(["/home/mihai/bin/mail", "list", "--limit", "3"],
                   capture_output=True, text=True, timeout=60)
lines.append("INBOX top3: " + r.stdout.replace("\n", " | ")[:300])

# PR 1489 status
req = urllib.request.Request("https://api.github.com/repos/xpaysh/awesome-x402/pulls/1489",
                             headers={"User-Agent": "Mozilla/5.0"})
d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
lines.append(f"PR1489: state={d.get('state')} mergeable={d.get('mergeable_state')} comments={d.get('comments')}")

# PR 830 status
req = urllib.request.Request("https://api.github.com/repos/apisyouwonthate/openapi.tools/pulls/830",
                             headers={"User-Agent": "Mozilla/5.0"})
d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
lines.append(f"PR830: state={d.get('state')} mergeable={d.get('mergeable_state')}")

# Frantic board movement
req = urllib.request.Request("https://gofrantic.com/v1/board", headers={"User-Agent": "vasilica-agent/0.1"})
d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
b = d["board"]
lines.append(f"FRANTIC: open={b.get('bounties_open')} funded=${b.get('funded_usd')} moved=${b.get('moved_usd')}")

# x402-list listing check
try:
    req = urllib.request.Request("https://x402-list.com/api/v1/services?limit=100",
                                 headers={"User-Agent": "Mozilla/5.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
    items = d.get("data", [])
    if isinstance(items, dict):
        items = items.get("items", [])
    hit = [it for it in items if "flowsentry" in json.dumps(it).lower()]
    lines.append(f"X402LIST: {len(items)} services online, flowsentry listed={len(hit)}")
except Exception as e:
    lines.append(f"X402LIST: ERR {str(e)[:60]}")

for l in lines:
    print(l)