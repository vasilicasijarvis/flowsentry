#!/usr/bin/env python3
"""Check PR #830 CI status (mergeable_state unstable)."""
import json
import subprocess


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)


def main():
    r = gh("pr", "view", "830", "--repo", "apisyouwonthate/openapi.tools", "--json",
           "statusCheckRollup,mergeStateStatus,comments")
    if r.returncode != 0:
        print("ERR", r.stderr[:300])
        return
    d = json.loads(r.stdout)
    for c in d.get("statusCheckRollup", []):
        print("check:", c.get("name"), "->", c.get("conclusion") or c.get("status"))
    for cm in d.get("comments", [])[-3:]:
        print("comment by", cm.get("author", {}).get("login"), ":", cm.get("body", "")[:300])
    print("mergeState:", d.get("mergeStateStatus"))


if __name__ == "__main__":
    main()