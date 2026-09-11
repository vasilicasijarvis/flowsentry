#!/usr/bin/env python3
"""PR attempt 2: branch from fork's own main, read fork README sha, then PR."""
import base64
import json
import subprocess

UPSTREAM = "repos/xpaysh/awesome-x402"
FORK = "repos/vasilicasijarvis/awesome-x402"
ENTRY = ("- [FlowSentry](https://flowsentry.vercel.app/api/scan) - Paid security scanner "
         "for n8n workflow JSON and MCP server configs. POST a workflow export, get findings "
         "ranked by severity: unauthenticated webhooks, hardcoded API keys, SSRF, command "
         "injection, 18 rules. $0.50 USDC per scan on Base (x402 v2, exact scheme), free demo "
         "scan via `X-FlowSentry-Demo: 1` header. Open-source CLI (Apache-2.0), listed in the "
         "official MCP Registry as `io.github.vasilicasijarvis/flowsentry`. "
         "([GitHub](https://github.com/vasilicasijarvis/flowsentry)) "
         "([PyPI](https://pypi.org/project/flowsentry/))")
BRANCH = "flowsentry-x402"


def gh(method, endpoint, payload=None):
    cmd = ["gh", "api", "-X", method, endpoint]
    if payload is not None:
        cmd += ["--input", "-"]
        r = subprocess.run(cmd, input=json.dumps(payload), capture_output=True, text=True, timeout=120)
    else:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"ERR {method} {endpoint}: {r.stderr[:200]}")
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return r.stdout


def main():
    # fork main branch sha
    ref = gh("GET", f"{FORK}/git/ref/heads/main")
    if not ref:
        raise SystemExit("no fork main")
    sha = ref["object"]["sha"]
    print("fork main sha:", sha[:12])

    # create branch
    gh("POST", f"{FORK}/git/refs", {"ref": f"refs/heads/{BRANCH}", "sha": sha})

    # read FORK readme (has own sha)
    d = gh("GET", f"{FORK}/contents/README.md?ref=main")
    if not d:
        raise SystemExit("cannot read fork README")
    fork_sha = d["sha"]
    readme = base64.b64decode(d["content"]).decode()

    if ENTRY in readme:
        print("entry already present in fork; aborting")
        return
    anchor = "- [Daizyx402 Security Research API](http://daizyx402.com:5402)"
    i = readme.find(anchor)
    if i < 0:
        print("ANCHOR NOT FOUND")
        return
    line_end = readme.find("\n", i)
    new = readme[:line_end + 1] + ENTRY + "\n" + readme[line_end + 1:]

    r = gh("PUT", f"{FORK}/contents/README.md", {
        "message": "Add FlowSentry (paid n8n/MCP security scans) to API Examples",
        "content": base64.b64encode(new.encode()).decode(),
        "branch": BRANCH,
        "sha": fork_sha,
    })
    print("commit:", "OK" if r else "FAILED")

    pr = gh("POST", f"{UPSTREAM}/pulls", {
        "title": "Add FlowSentry: paid security scans for n8n workflows (x402)",
        "head": f"vasilicasijarvis:{BRANCH}",
        "base": "main",
        "body": ("Adds FlowSentry to **API Examples** (after Daizyx402, alphabetical).\n\n"
                 "What it is: a paid (x402, 0.50 USDC/scan on Base) security scanner for "
                 "n8n workflow JSON and MCP server configs - POST a workflow export, get "
                 "findings ranked by severity (unauthenticated webhooks, hardcoded API keys, "
                 "SSRF, command injection - 18 rules). Free demo scan via "
                 "`X-FlowSentry-Demo: 1` header. Open-source CLI (Apache-2.0), listed in the "
                 "official MCP Registry as `io.github.vasilicasijarvis/flowsentry`, on PyPI "
                 "as `flowsentry`.\n\n"
                 "Fits the list's Agent Verification & Security theme from the deployable-"
                 "artifact side: it checks the workflows and MCP configs agents actually "
                 "run, not the payments they make.\n\n"
                 "Links in the entry are live: API (402 + demo header verified today), "
                 "GitHub repo, PyPI package."),
    })
    if isinstance(pr, dict) and pr.get("number"):
        print("PR OPENED:", pr.get("html_url"))
    else:
        print("PR resp:", str(pr)[:300])


if __name__ == "__main__":
    main()