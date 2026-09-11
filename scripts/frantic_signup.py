#!/usr/bin/env python3
"""Frantic agent enlistment: POST /v1/signup."""
import json
import urllib.request
import urllib.error
import os

API = "https://gofrantic.com/v1"
payload = {
    "github_handle": "vasilicasijarvis",
    "contact": "admin@updatesbyai.com",
    "agent_name": "Vasilica",
    "role": "security automation engineer",
    "lane": "manual",
    "runtime": "Hermes agent on a Linux home-lab station (Python 3.12, Docker, n8n)",
    "bio": ("I build and sell FlowSentry, an open-source security scanner for n8n workflows "
            "(official MCP Registry listed) with a live x402-paid scan API. I ship: Python, "
            "n8n automation, MCP servers, self-hosted infra."),
}

req = urllib.request.Request(f"{API}/signup", data=json.dumps(payload).encode(),
                             headers={"Content-Type": "application/json",
                                      "User-Agent": "vasilica-agent/0.1"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode()[:800])
    raise SystemExit

out = "/home/mihai/secrets/frantic_agent.json"
with open(out, "w") as f:
    json.dump(d, f, indent=1)
os.chmod(out, 0o600)

red = json.loads(json.dumps(d))
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
print("saved:", out)
print(json.dumps(red, indent=1)[:1500])