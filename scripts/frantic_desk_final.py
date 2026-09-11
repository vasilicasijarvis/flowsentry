#!/usr/bin/env python3
"""Last desk-signin attempt + 5min poll for this run."""
import json
import re
import subprocess
import time
import urllib.request

# one more trigger
req = urllib.request.Request(
    "https://gofrantic.com/v1/desk/signin",
    data=json.dumps({"contact": "admin@updatesbyai.com"}).encode(),
    headers={"Content-Type": "application/json", "User-Agent": "vasilica-agent/0.1"},
    method="POST")
with urllib.request.urlopen(req, timeout=60) as r:
    print("trigger:", r.status)

deadline = time.time() + 300
found = False
while time.time() < deadline and not found:
    rr = subprocess.run(["/home/mihai/bin/mail", "list", "--limit", "4"],
                        capture_output=True, text=True, timeout=60)
    for line in rr.stdout.splitlines():
        low = line.lower()
        if "gofrantic" in low and "verify" not in low:
            mid = line.split("]")[0].strip("[")
            read = subprocess.run(["/home/mihai/bin/mail", "read", mid],
                                  capture_output=True, text=True, timeout=60)
            m = re.search(r'https://gofrantic\.com/[^\s"\']+', read.stdout)
            if m:
                print("DESK LINK:", m.group(0))
                found = True
                break
    if not found:
        time.sleep(30)
if not found:
    print("still nothing after 5 min — defer to next run")