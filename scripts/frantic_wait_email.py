#!/usr/bin/env python3
"""Wait for Frantic desk sign-in email (poll inbox up to 90s)."""
import subprocess
import time

deadline = time.time() + 90
while time.time() < deadline:
    r = subprocess.run(["/home/mihai/bin/mail", "list", "--limit", "3"],
                       capture_output=True, text=True, timeout=60)
    if "gofrantic" in r.stdout.lower() and "desk" in r.stdout.lower() or \
       "sign in" in r.stdout.lower():
        print("FOUND:")
        print(r.stdout[:400])
        raise SystemExit
    time.sleep(10)
print("not yet; latest:")
print(r.stdout[:400])