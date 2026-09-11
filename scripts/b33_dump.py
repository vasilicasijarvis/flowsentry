#!/usr/bin/env python3
"""Dump full description of Frantic bounty 33."""
import json

d = json.load(open("/tmp/b33.json"))
b = d["bounty"]
print(b["description"])
print("---- acceptance:", b.get("acceptance") or b.get("acceptance_criteria"))
print("---- slots:", b.get("claim_slots"))
print("---- actions:", json.dumps(b.get("actions"), indent=1)[:500])