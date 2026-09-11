#!/usr/bin/env python3
"""List _data dir of openapi.tools repo."""
import json
import urllib.request

req = urllib.request.Request(
    "https://api.github.com/repos/apisyouwonthate/openapi.tools/contents/_data",
    headers={"User-Agent": "Mozilla/5.0"})
d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
for x in d:
    print(x["name"], x.get("size"))