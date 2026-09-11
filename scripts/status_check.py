#!/usr/bin/env python3
"""Check n8n Jobs threads + inbox. Reusable monitor (fixes /t/{id}.json 422)."""
import json
import urllib.request

BASE = "https://community.n8n.io"


def http(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()


def discourse_topics():
    out = {}
    for tid in ("311286", "312281", "312357"):
        # print=true returns ALL posts (plain .json can 422 / truncate)
        url = f"{BASE}/t/{tid}.json?print=true&track_visit=false"
        try:
            data = json.loads(http(url))
            posts = data.get("post_stream", {}).get("posts", [])
            mine = [p for p in posts if p.get("username") == "vasilicasijarvis"]
            last = posts[-1]["post_number"] if posts else 0
            last_by = posts[-1].get("username") if posts else "-"
            recent = []
            for p in posts[-8:]:
                recent.append(f"#{p['post_number']} by {p.get('username')}: "
                              f"{(p.get('cooked') or '')[:80].replace(chr(10),' ')}")
            out[tid] = {
                "title": data.get("title", "")[:60], "views": data.get("views"),
                "last_post": last, "last_by": last_by, "my_posts": len(mine),
                "my_last": mine[-1]["post_number"] if mine else None,
                "recent": recent,
            }
        except Exception as e:
            out[tid] = f"ERR {str(e)[:80]}"
    return out


def fresh_jobs():
    """Latest Jobs-category topics (id 13)."""
    try:
        data = json.loads(http(f"{BASE}/c/13.json?order=created"))
        topics = []
        for t in data.get("topic_list", {}).get("topics", []):
            created = t.get("created_at", "")[:10]
            topics.append(f"[{created}] {t['id']} {t['title'][:70]} (posts={t.get('posts_count')})")
        return topics[:12]
    except Exception as e:
        return f"ERR {str(e)[:80]}"


def directories():
    out = {}
    for name, url in [
        ("mcp.directory", "https://mcp.directory/servers/flowsentry"),
        ("registry", "https://registry.modelcontextprotocol.io/v0.1/servers?search=vasilicasijarvis"),
    ]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read().decode()
                out[name] = r.status if name != "registry" else (
                    "ACTIVE" if "flowsentry" in body.lower() else "MISSING")
        except Exception as e:
            out[name] = f"ERR {str(e)[:40]}"
    return out


def inbox():
    try:
        res = subprocess_run()
        lines = [l for l in res.splitlines() if l.strip()]
        return f"{len(lines)} emails; newest: {lines[0][:100] if lines else 'none'}"
    except Exception as e:
        return f"ERR {e}"


def subprocess_run():
    import subprocess
    res = subprocess.run(["/home/mihai/bin/mail", "list"], capture_output=True, text=True, timeout=30)
    return res.stdout


if __name__ == "__main__":
    print("== Discourse threads ==")
    print(json.dumps(discourse_topics(), indent=1))
    print("== Fresh Jobs topics ==")
    for t in fresh_jobs():
        print(" ", t)
    print("== MCP directories ==")
    print(json.dumps(directories(), indent=1))
    print("== Inbox ==")
    print(inbox())