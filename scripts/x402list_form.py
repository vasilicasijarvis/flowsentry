#!/usr/bin/env python3
"""Extract exact form field names from x402-list.com/submit."""
import re
import urllib.request

req = urllib.request.Request("https://x402-list.com/submit", headers={"User-Agent": "Mozilla/5.0"})
body = urllib.request.urlopen(req, timeout=45).read().decode()

fields = re.findall(r'<(input|textarea|select)[^>]*name="([^"]+)"[^>]*>', body)
print("fields:", fields)

# category options
m = re.search(r'name="category".*?</select>', body, re.S)
if m:
    opts = re.findall(r'<option value="([^"]*)"', m.group(0))
    print("category options:", opts)

# endpoint textarea hint
m = re.search(r'id="endpoints-hint"[^>]*>([^<]*)<', body)
print("endpoints hint:", m.group(1) if m else None)

# form action
m = re.search(r'<form[^>]*>', body)
print("form tag:", m.group(0)[:300] if m else "NO FORM")

# website field hint text
m = re.search(r'website[^>]*hint[^>]*>([^<]*)<', body, re.I)
print("website hint:", m.group(1) if m else None)