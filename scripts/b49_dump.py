#!/usr/bin/env python3
"""Dump Frantic bounty 49 (Give runx some love)."""
import json

d = json.load(open("/tmp/b49.json"))
b = d["bounty"]
print(b.get("title"), "| $", b.get("price_usd"))
print(b.get("description", "")[:2500])