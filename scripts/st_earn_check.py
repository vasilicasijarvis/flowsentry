#!/usr/bin/env python3
"""Fetch Superteam Earn listings and print a compact digest."""
import json
import urllib.request

URL = "https://superteam.fun/api/listings"


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    lst = d if isinstance(d, list) else d.get("data", d.get("listings", []))
    print("total:", len(lst))
    for x in lst[:25]:
        print(x.get("id"), "|", (x.get("title") or "")[:58],
              "|", x.get("type"), "|", x.get("rewardAmount"), x.get("rewardToken", ""),
              "|", x.get("agentAccess"), "|",
              (x.get("deadline") or "")[:10], "|", x.get("status"))


if __name__ == "__main__":
    main()