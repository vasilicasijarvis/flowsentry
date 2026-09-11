#!/usr/bin/env python3
"""Check if my x402-list submission persisted: look for pending/recent submissions."""
import json
import urllib.request
import urllib.error

ENDPOINTS = [
    "https://x402-list.com/api/v1/services?status=pending",
    "https://x402-list.com/api/v1/services?sort=newest",
    "https://x402-list.com/api/v1/services?limit=100",
]

for url in ENDPOINTS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=40).read().decode())
        items = data.get("data", data)
        if isinstance(items, dict):
            items = items.get("items", items.get("services", []))
        print(url.split("?")[1], "-> items:", len(items))
        if items:
            for it in items[:5]:
                if isinstance(it, dict):
                    print("  sample:", it.get("name") or it.get("service_name"),
                          "|", it.get("status"), "|", (it.get("website_url") or it.get("url") or "")[:50])
        low = json.dumps(data).lower()
        print("  flowsentry present:", "flowsentry" in low)
    except urllib.error.HTTPError as e:
        print(url, "HTTP", e.code)
    except Exception as e:
        print(url, "ERR", str(e)[:80])