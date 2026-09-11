#!/usr/bin/env python3
"""Status snapshot for the n8n Jobs pipeline + MCP directories + inbox.

Run: python3 scripts/status_check.py
Prints: my Discourse posts + thread stats, MCP directory listing checks, inbox count.
"""
import json
import subprocess
import urllib.request

N8N = "https://community.n8n.io"
MY_USER = "vasilicasijarvis"


def discourse_topics():
    """Unauthenticated /t/{id}.json only returns the first chunk; my posts may live
    beyond it. Use ?print=true which returns ALL posts, then filter."""
    topics = {}
    for tid in [311286, 312281, 312357]:
        try:
            with urllib.request.urlopen(f"{N8N}/t/{tid}.json?print=true", timeout=30) as r:
                j = json.loads(r.read().decode())
            posts = j.get("post_stream", {}).get("posts", [])
            mine = [p for p in posts if p.get("username") == MY_USER]
            topics[tid] = {
                "title": j.get("title", "")[:50],
                "views": j.get("views"),
                "posts": j.get("posts_count"),
                "my_last": max((p["post_number"] for p in mine), default=None),
                "my_posts": len(mine),
            }
        except Exception as e:
            topics[tid] = {"error": str(e)[:60]}
    return topics


def directories():
    out = {}
    for name, url in [
        ("mcp.directory", "https://mcp.directory/servers/flowsentry"),
        ("mcpservers.org", "https://mcpservers.org/search?q=flowsentry"),
        ("registry", "https://registry.modelcontextprotocol.io/v0.1/servers?search=vasilicasijarvis"),
    ]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read().decode()
                out[name] = r.status if name != "registry" else ("ACTIVE" if "flowsentry" in body.lower() else "MISSING")
        except Exception as e:
            out[name] = f"ERR {str(e)[:40]}"
    return out


def inbox():
    try:
        res = subprocess.run(["/home/mihai/bin/mail", "list"], capture_output=True, text=True, timeout=30)
        lines = [l for l in res.stdout.splitlines() if l.strip()]
        return f"{len(lines)} emails; newest: {lines[0][:80] if lines else 'none'}"
    except Exception as e:
        return f"ERR {e}"


if __name__ == "__main__":
    print("== Discourse threads ==")
    print(json.dumps(discourse_topics(), indent=1))
    print("== MCP directories ==")
    print(json.dumps(directories(), indent=1))
    print("== Inbox ==")
    print(inbox())