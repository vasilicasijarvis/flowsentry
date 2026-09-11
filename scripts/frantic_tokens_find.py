#!/usr/bin/env python3
"""Find where the Frantic tokens live (file was overwritten by seals poll)."""
import json

for path in ("/home/mihai/secrets/frantic_agent.json",
             "/home/mihai/secrets/frantic_agent_status.json"):
    try:
        d = json.load(open(path))
        print(path, "->", list(d.keys()))
    except Exception as e:
        print(path, "ERR", e)

# search for the tokens anywhere in secrets
import glob
for p in ("/home/mihai/secrets/*.json",):
    import glob as g
    for f in g.glob(p):
        try:
            raw = open(f).read()
        except Exception:
            continue
        for kw in ("fr_age", "fr_op_", "agent-a3ea73"):
            if kw in raw:
                print(f, "contains", kw)