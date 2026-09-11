#!/usr/bin/env python3
"""Poll Frantic desk signin email up to 4 min (background-friendly single run)."""
import re
import subprocess
import time

deadline = time.time() + 240
found = False
while time.time() < deadline and not found:
    r = subprocess.run(["/home/mihai/bin/mail", "list", "--limit", "4"],
                       capture_output=True, text=True, timeout=60)
    for line in r.stdout.splitlines():
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
        time.sleep(25)
if not found:
    print("no desk email in 4 min — leave for next run")