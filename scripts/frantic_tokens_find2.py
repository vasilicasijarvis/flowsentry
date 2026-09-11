#!/usr/bin/env python3
"""Search workspace + shell history for saved Frantic tokens."""
import glob
import json

hits = []
for pattern in ("/home/mihai/flowsentry/**/*.json", "/home/mihai/secrets/*.json",
                "/tmp/frantic*", "/home/mihai/.hermes/**/*.json"):
    for f in glob.glob(pattern, recursive=True)[:200]:
        try:
            raw = open(f).read()
        except Exception:
            continue
        if "fr_age" in raw or "fr_op_" in raw:
            hits.append(f)
print("token files:", hits)

# check if tokens are in the original signup stdout saved anywhere else
for f in glob.glob("/tmp/*.json") + glob.glob("/tmp/*signup*"):
    try:
        raw = open(f).read()
    except Exception:
        continue
    if "fr_age" in raw:
        print("TMP HIT:", f)