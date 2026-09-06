#!/usr/bin/env python3
"""Fetch subreddit rules for r/n8n and r/selfhosted before drafting posts."""

import json
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) FlowSentryResearch/0.1"}

for sub in ("n8n", "selfhosted"):
    url = f"https://www.reddit.com/r/{sub}/about/rules.json"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
        print(f"=== r/{sub} rules ===")
        for r in data.get("rules", []):
            print(f"  RULE: {r.get('short_name')} - {str(r.get('description', ''))[:200]}")
    except Exception as exc:
        print(f"=== r/{sub} rules: FAILED - {exc}")
    print()
