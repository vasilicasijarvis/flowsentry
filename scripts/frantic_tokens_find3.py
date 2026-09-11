#!/usr/bin/env python3
"""Search ALL of secrets + flowsentry scripts dir for the Frantic token strings."""
import glob
import os

for root in ("/home/mihai/secrets", "/home/mihai/flowsentry/scripts",
             "/home/mihai/flowsentry", "/tmp"):
    for f in glob.glob(os.path.join(root, "**", "*"), recursive=True):
        if not os.path.isfile(f) or os.path.getsize(f) > 2_000_000:
            continue
        try:
            raw = open(f, errors="ignore").read()
        except Exception:
            continue
        if "fr_age" in raw or "fr_op_" in raw:
            print("HIT:", f)
            i = raw.find("fr_age")
            if i < 0:
                i = raw.find("fr_op_")
            print("   ctx:", raw[max(0, i - 60):i + 60].replace("\n", " "))