#!/usr/bin/env python3
"""Verify x402-list submission landed (look for success markers on submit page / service search)."""
import re
import urllib.request
import urllib.error
import json

# 1) re-fetch submit page for a success banner pattern
req = urllib.request.Request("https://x402-list.com/submit", headers={"User-Agent": "Mozilla/5.0"})
body = urllib.request.urlopen(req, timeout=45).read().decode()
for kw in ("received", "success", "thank", "reviewed"):
    m = re.search(kw, body, re.I)
    if m:
        print(f"[{kw}]", body[max(0, m.start() - 80):m.start() + 180].replace("\n", " ")[:240])

# 2) search the directory for flowsentry
for url in ("https://x402-list.com/api/v1/services?q=flowsentry",
            "https://x402-list.com/api/v1/services?query=flowsentry",
            "https://x402-list.com/api/v1/services/search?q=flowsentry"):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        s = json.dumps(data)
        print(url.split('.com')[1], "-> flowsentry hits:", s.lower().count("flowsentry"),
              "| items:", len(data) if isinstance(data, list) else list(data.keys())[:6])
    except urllib.error.HTTPError as e:
        print(url.split('.com')[1], "HTTP", e.code)
    except Exception as e:
        print(url.split('.com')[1], "ERR", str(e)[:80])