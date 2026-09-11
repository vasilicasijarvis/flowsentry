#!/usr/bin/env python3
"""Retry desk signin + long poll (up to 8 min) for the operator link."""
import re
import subprocess
import time
import urllib.request

def req_desk():
    req = urllib.request.Request(
        "https://gofrantic.com/v1/desk/signin",
        data=json.dumps({"contact": "admin@updatesbyai.com"}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "vasilica-agent/0.1"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode()[:120]

import json
print("retry:", req_desk())

deadline = time.time() + 480
found = False
while time.time() < deadline and not found:
    r = subprocess.run(["/home/mihai/bin/mail", "list", "--limit", "3"],
                       capture_output=True, text=True, timeout=60)
    for line in r.stdout.splitlines():
        low = line.lower()
        if "gofrantic" in low and "verify" not in low:
            mid = line.split("]")[0].strip("[")
            read = subprocess.run(["/home/mihai/bin/mail", "read", mid],
                                  capture_output=True, text=True, timeout=60)
            m = re.search(r'https://gofrantic\.com/[^\s"\']+', read.stdout)
            if m:
                print("MAIL", mid, "->", m.group(0))
                found = True
                break
    if not found:
        time.sleep(30)
if not found:
    print("no desk email after 8 min")