#!/usr/bin/env python3
"""Probe flowsentry scan endpoint: which payloads trigger the 402 payment flow."""
import json
import urllib.error
import urllib.request

BASE = "https://flowsentry.vercel.app/api/scan"


def post(body, headers=None):
    data = json.dumps(body).encode()
    h = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(BASE, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, dict(r.headers), r.read().decode()[:400]
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()[:400]


WF = {"workflow": {"nodes": [
    {"name": "Webhook", "type": "n8n-nodes-base.webhook", "parameters": {"httpMethod": "GET", "path": "hook"}},
    {"name": "Set", "type": "n8n-nodes-base.set", "parameters": {}},
]}}

cases = [
    ("workflow+target_url", {"workflow": WF["workflow"], "target_url": "http://example.com"}, None),
    ("workflow only", WF, None),
    ("bare export", WF["workflow"], None),
]
for name, body, hdr in cases:
    st, hd, txt = post(body, hdr)
    pr = "X-PAYMENT-REQUIRED" in hd or "PAYMENT-REQUIRED" in hd
    print(f"{name}: {st} 402hdr={pr} body={txt[:150]}")

# demo scan on a workflow payload
st, hd, txt = post(WF, {"X-FlowSentry-Demo": "1"})
print("demo workflow scan:", st, txt[:300])
print("  findings in response:", '"findings"' in txt)