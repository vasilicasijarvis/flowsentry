#!/usr/bin/env python3
"""Check x402 scan endpoint status (payments LIVE, Bazaar indexed, demo mode)."""
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
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, dict(r.headers), r.read().decode()[:600]
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()[:600]


if __name__ == "__main__":
    st, hd, body = post({"target_url": "http://example.com"})
    print("POST info:", st)
    print("  X-PAYMENT-REQUIRED present:", "X-PAYMENT-REQUIRED" in hd)
    print("  Bazaar header:", (hd.get("X-402-DISCOVERY") or hd.get("x-402-discovery") or "none")[:120])
    demo = post({"target_url": "http://example.com"}, {"X-FlowSentry-Demo": "1"})
    print("Demo scan:", demo[0], demo[2][:200])
    bazaar = urllib.request.urlopen(
        "https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources?q=flowsentry",
        timeout=30).read().decode()
    print("Bazaar catalog:", bazaar[:300])