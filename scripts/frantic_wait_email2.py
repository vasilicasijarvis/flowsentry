#!/usr/bin/env python3
"""Poll for Frantic desk sign-in email up to 3 min; print verification link if found."""
import re
import subprocess
import time

deadline = time.time() + 180
found = False
while time.time() < deadline and not found:
    r = subprocess.run(["/home/mihai/bin/mail", "list", "--limit", "3"],
                       capture_output=True, text=True, timeout=60)
    for line in r.stdout.splitlines():
        if "gofrantic" in line.lower() and "verify" not in line.lower():
            mid = line.split("]")[0].strip("[")
            read = subprocess.run(["/home/mihai/bin/mail", "read", mid],
                                  capture_output=True, text=True, timeout=60)
            m = re.search(r'https://gofrantic\.com/[^\s"\']+', read.stdout)
            if m:
                print("MAIL", mid, "->", m.group(0))
                found = True
                break
    if not found:
        time.sleep(20)
if not found:
    print("no desk email after 3 min")