#!/usr/bin/env python3
"""Final desk-signin retry; then update skill with Frantic + x402-list knowledge."""
import json
import urllib.request

req = urllib.request.Request(
    "https://gofrantic.com/v1/desk/signin",
    data=json.dumps({"contact": "admin@updatesbyai.com"}).encode(),
    headers={"Content-Type": "application/json", "User-Agent": "vasilica-agent/0.1"},
    method="POST")
with urllib.request.urlopen(req, timeout=60) as r:
    print("retry desk signin:", r.status)
print("(check inbox in the next minutes; recovery path documented in skill)")