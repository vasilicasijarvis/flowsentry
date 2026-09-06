"""Verify flowsentry exists on PyPI by querying the JSON API (stdlib only)."""
import json
import sys
import urllib.request

name = sys.argv[1] if len(sys.argv) > 1 else "flowsentry"
url = "https://pypi.org/pypi/%s/json" % name
with urllib.request.urlopen(url, timeout=30) as resp:
    data = json.load(resp)

info = data["info"]
print("NAME:", info["name"])
print("VERSION:", info["version"])
print("SUMMARY:", info["summary"])
print("AUTHOR:", info.get("author") or info.get("author_email"))
print("REQUIRES_PYTHON:", info.get("requires_python"))
print("PROJECT_URLS:", info.get("project_urls"))
print("RELEASE FILES:")
for version, files in sorted(data["releases"].items()):
    for f in files:
        print("  ", version, f["filename"], f["size"], "bytes")
