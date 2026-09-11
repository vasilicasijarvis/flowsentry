#!/usr/bin/env python3
"""Open PR on apisyouwonthate/openapi.tools adding flowsentry.md."""
import base64
import json
import subprocess

UPSTREAM = "repos/apisyouwonthate/openapi.tools"
FORK = "repos/vasilicasijarvis/openapi.tools"
BRANCH = "flowsentry-docs-entry"
TOOL_MD = open("/tmp/flowsentry_tool.md").read()


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
    # fork
    gh("POST", f"{UPSTREAM}/forks", {})
    import time
    time.sleep(3)

    # base branch sha on fork
    ref = gh("GET", f"{FORK}/git/ref/heads/main")
    if not ref:
        raise SystemExit("fork main missing")
    sha = ref["object"]["sha"]
    print("fork main:", sha[:10])

    # create branch (tolerate exists)
    r = gh("POST", f"{FORK}/git/refs", {"ref": f"refs/heads/{BRANCH}", "sha": sha})
    if r is None:
        print("branch exists or error (continuing)")

    # commit new file
    r = gh("PUT", f"{FORK}/contents/src/content/tools/flowsentry.md", {
        "message": "Add FlowSentry: security scanner for n8n/MCP workflow configs",
        "content": base64.b64encode(TOOL_MD.encode()).decode(),
        "branch": BRANCH,
    })
    print("commit:", "OK" if r else "FAILED")

    # PR
    pr = gh("POST", f"{UPSTREAM}/pulls", {
        "title": "Add FlowSentry (security scanner for n8n workflow JSON + MCP configs)",
        "head": f"vasilicasijarvis:{BRANCH}",
        "base": "main",
        "body": ("Adds FlowSentry under `security` + `schema-validators` categories.\n\n"
                 "**What it is:** open-source (Apache-2.0) static-analysis security scanner "
                 "for n8n workflow exports and MCP server configs - 18 rules covering "
                 "unauthenticated webhooks, hardcoded API keys, SSRF, command injection; "
                 "findings ranked by severity; JSON/SARIF/HTML reports. Ships as a "
                 "zero-dependency Python CLI (`flowsentry` on PyPI), a GitHub repo with CI, "
                 "and an MCP server listed in the official MCP Registry "
                 "(`io.github.vasilicasijarvis/flowsentry`).\n\n"
                 "**Relevance to the OpenAPI ecosystem:** n8n workflows embed HTTP Request "
                 "nodes with OpenAPI-style operations; MCP tool schemas mirror OpenAPI "
                 "surface conventions, and the project documents its own paid scan API with "
                 "an OpenAPI-style schema. Teams that keep API specs in sync with automation "
                 "stacks can scan the workflow side with the same rigor.\n\n"
                 "**Testable:** `pip install flowsentry` then "
                 "`flowsentry scan workflow.json` - or run the zero-dep CLI from the repo. "
                 "Live scan API + free demo header documented at the landing link.\n\n"
                 "**Real-world use:** published on PyPI (0.1.0), listed in the official MCP "
                 "Registry, CI self-scan green on the public repo."),
    })
    if isinstance(pr, dict) and pr.get("number"):
        print("PR OPENED:", pr.get("html_url"))
    else:
        print("PR resp:", str(pr)[:300])


if __name__ == "__main__":
    main()