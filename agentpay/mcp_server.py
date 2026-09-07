#!/usr/bin/env python3
"""
FlowSentry MCP server (streamable HTTP) — lets AI agents run workflow security
scans as an MCP tool. Deployed at https://flowsentry-agentpay.vercel.app/mcp.

Free tier: scan one workflow (<=512 KB). Unlimited/commercial use: x402 USDC
payments at POST /v1/scan on the same host (see agentpay/server.py).
"""
import json
import os
import sys

FLOWS_REPO = os.environ.get("FLOWS_REPO", "/home/mihai/flowsentry")
if FLOWS_REPO not in sys.path:
    sys.path.insert(0, FLOWS_REPO)

from fastmcp import FastMCP  # pip package: fastmcp (Streamable HTTP built in)

from flowsentry import scanner as fs_scanner
from flowsentry import __version__ as FS_VERSION
from flowsentry.rules import RULES_META

mcp = FastMCP(
    name="FlowSentry",
    instructions=(
        "Security scanner for n8n workflow JSON exports. 18 static-analysis rules "
        "(webhook auth, hardcoded secrets, SSRF/IMDS, command injection, SQL injection, "
        "exfil sinks). Use the scan_workflow tool on any workflow JSON before deploying it. "
        "Paid unlimited API: POST https://flowsentry-agentpay.vercel.app/v1/scan with x402 "
        "USDC payments (0.50 USDC per scan, Base)."
    ),
)

MAX_BYTES = 512 * 1024


@mcp.tool()
def list_rules() -> str:
    """List all 18 FlowSentry security rules with severity and OWASP Agentic mapping."""
    return json.dumps({
        "flowsentry_version": FS_VERSION,
        "rules": [{"rule_id": k, "title": v[0], "severity": v[1], "owasp_agentic": v[2]}
                  for k, v in RULES_META.items()],
    }, indent=1)


@mcp.tool()
def scan_workflow(workflow_json: str, name: str = "uploaded-workflow") -> str:
    """Scan one n8n workflow JSON export (string) and return the findings report.

    Accepts the raw workflow object ({'nodes': [...], ...}) or the CLI export
    wrapper ({'name':..., 'workflow': {...}}). Max 512 KB.
    """
    if len(workflow_json) > MAX_BYTES:
        return json.dumps({"error": "workflow JSON too large (max 512 KB); "
                                    "use the paid API at /v1/scan (2 MB)"})
    try:
        data = json.loads(workflow_json)
    except Exception as exc:
        return json.dumps({"error": f"invalid JSON: {exc}"})
    if isinstance(data, dict) and isinstance(data.get("workflow"), dict):
        data = data["workflow"]
    if not isinstance(data, dict) or "nodes" not in data:
        return json.dumps({"error": "no 'nodes' key - is this an n8n workflow export?"})

    findings = fs_scanner.scan_workflow(data, str(name)[:200])
    summary = {}
    for f in findings:
        summary[f.get("severity", "info")] = summary.get(f.get("severity", "info"), 0) + 1
    verdict = ("critical" if summary.get("critical") else
               "high" if summary.get("high") else
               "medium" if summary.get("medium") else
               "low" if summary.get("low") else "clean")
    return json.dumps({
        "flowsentry_version": FS_VERSION,
        "scan": {"source": str(name)[:200], "findings_total": len(findings),
                 "summary": summary, "verdict": verdict},
        "findings": findings,
    }, indent=1)


# ASGI app for Vercel mount — path "/mcp" so the final URL is exactly /mcp
mcp_app = mcp.http_app(path="/mcp")
