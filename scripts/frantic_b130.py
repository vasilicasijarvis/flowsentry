#!/usr/bin/env python3
"""Read Frantic bounty 130 full description + claim requirements."""
import json
import urllib.request

req = urllib.request.Request("https://gofrantic.com/v1/bounties/130",
                             headers={"User-Agent": "vasilica-agent/0.1"})
d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
b = d["bounty"]
print(b["description"])