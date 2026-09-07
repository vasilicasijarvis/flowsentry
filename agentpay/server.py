#!/usr/bin/env python3
"""
FlowSentry AgentPay — paid security-scan API for AI agents, using the x402 protocol.

Flow (x402 v2, HTTP transport):
  1. Agent POSTs workflow JSON to /v1/scan with no payment
  2. Server answers 402 + PAYMENT-REQUIRED header (base64 PaymentRequired object)
  3. Agent signs USDC payment (EIP-3009) and retries with PAYMENT-SIGNATURE header
  4. x402.org facilitator verifies + settles payment on Base Sepolia
  5. Server runs FlowSentry (18 rules) and returns the JSON report + PAYMENT-RESPONSE header

Runs standalone (uvicorn) or as a Vercel Python serverless function.
Env vars:
  FLOWSOWNER_ADDR   receiver EVM address (required for payments)
  NETWORK           CAIP-2 network, default eip155:84532 (Base Sepolia)
  PRICE_USD         price per scan, default "0.50"
  FACILITATOR_URL   default https://x402.org/facilitator
  FLOWS_REPO        path to flowsentry checkout (local mode), default /home/mihai/flowsentry
"""
import base64
import importlib
import json
import os
import sys

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from x402 import x402ResourceServer
from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption, RouteConfig
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.http.middleware._bazaar_utils import register_bazaar_extension

# Bazaar discovery declaration (x402 v2 extension): lets facilitators catalog
# POST /v1/scan so agents can find it via Bazaar search/discovery APIs.
BODY_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Optional workflow name"},
        "nodes": {"type": "array", "items": {"type": "object"},
                  "description": "n8n workflow nodes array"},
        "connections": {"type": "object", "description": "n8n connections object"},
    },
    "required": ["nodes"],
}
BAZAAR_DECLARATION = {
    "info": {
        "input": {
            "type": "http", "method": "POST", "bodyType": "json",
            "body": {"name": "my-workflow",
                     "nodes": [{"name": "Webhook", "type": "n8n-nodes-base.webhook",
                                "parameters": {"authentication": "none"}}],
                     "connections": {}},
        },
        "output": {
            "type": "json",
            "example": {"scan": {"source": "my-workflow", "findings_total": 3,
                                 "summary": {"critical": 2, "medium": 1},
                                 "verdict": "critical"},
                        "findings": [{"rule_id": "FS001", "severity": "critical",
                                      "title": "Webhook endpoint without authentication"}]},
        },
    },
    "schema": {
        "type": "object",
        "properties": {
            "input": {"type": "object",
                      "properties": {"type": {"type": "string", "enum": ["http"]},
                                     "method": {"type": "string", "enum": ["POST"]},
                                     "bodyType": {"type": "string", "enum": ["json"]},
                                     "body": BODY_SCHEMA},
                      "required": ["type", "method", "body"]},
            "output": {"type": "object",
                       "properties": {"type": {"type": "string"},
                                      "example": {"type": "object"}}},
        },
        "required": ["input"],
    },
}

try:
    from agentpay.mcp_server import mcp_app
except Exception as _mcp_exc:
    mcp_app = None
    _MCP_ERR = repr(_mcp_exc)
else:
    _MCP_ERR = None

# ---------------------------------------------------------------- FlowSentry import
FLOWS_REPO = os.environ.get("FLOWS_REPO", "/home/mihai/flowsentry")
if FLOWS_REPO not in sys.path:
    sys.path.insert(0, FLOWS_REPO)
try:
    from flowsentry import scanner as fs_scanner
    from flowsentry import __version__ as FS_VERSION
except Exception as _exc:  # pragma: no cover
    fs_scanner = None
    FS_VERSION = "unavailable"
    _IMPORT_ERR = repr(_exc)
else:
    _IMPORT_ERR = None

# ---------------------------------------------------------------- Config
OWNER_ADDR = os.environ.get("FLOWSOWNER_ADDR", "")
NETWORK = os.environ.get("NETWORK", "eip155:84532")          # Base Sepolia
PRICE_USD = os.environ.get("PRICE_USD", "0.50")
FACILITATOR_URL = os.environ.get("FACILITATOR_URL", "https://x402.org/facilitator")
MAX_BODY_BYTES = 2 * 1024 * 1024                             # 2 MB workflow cap
SVC = "flowsentry-agentpay"

WELL_KNOWN = {
    "type": "https://erc8004.spec/schema/v1/agent-registration.json",
    "name": "FlowSentry",
    "description": ("Security scanner for n8n workflow JSON exports: 18 static-analysis "
                    "rules (webhook auth, hardcoded secrets, SSRF/IMDS, command injection, "
                    "SQL injection, exfil sinks). Paid per-scan over x402 USDC."),
    "version": "0.2.0",
    "endpoints": [{"name": "agentpay-x402",
                   "endpoint": os.environ.get("PUBLIC_BASE_URL", "https://TBD/x402"),
                   "capabilities": ["scan", "x402"]}],
    "x402Support": True,
    "active": True,
    "registrations": [],
    "supportedTrust": [],
}

app = FastAPI(title="FlowSentry AgentPay", version="0.2.0",
              description="n8n workflow security scans, paid per request with USDC over x402")

# ---------------------------------------------------------------- Free endpoints
@app.get("/health")
def health():
    return {
        "service": SVC, "status": "ok" if (fs_scanner and OWNER_ADDR) else "degraded",
        "flowsentry_version": FS_VERSION, "scanner_loaded": fs_scanner is not None,
        "scanner_import_error": _IMPORT_ERR,
        "receiver_address": OWNER_ADDR or "NOT_CONFIGURED",
        "network": NETWORK, "price_per_scan_usd": PRICE_USD,
        "facilitator": FACILITATOR_URL, "protocol": "x402-v2/http",
    }

@app.get("/v1/rules")
def rules():
    """Free: what the scan checks, so agents can decide."""
    if not fs_scanner:
        return JSONResponse({"error": "scanner unavailable"}, status_code=503)
    from flowsentry.rules import RULES_META
    return {"rules": RULES_META, "count": len(RULES_META)}

@app.get("/.well-known/agent-registration.json")
def agent_registration():
    return JSONResponse(WELL_KNOWN)

@app.get("/x402/info")
def x402_info():
    """Machine-readable payment terms (some agents probe this before the 402 dance)."""
    return {
        "protocol": "x402", "version": 2, "transport": "http",
        "resource": "POST /v1/scan", "accepts": [{
            "scheme": "exact", "network": NETWORK,
            "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",  # USDC Base Sepolia
            "payTo": OWNER_ADDR, "price": PRICE_USD + " USD",
        }],
        "how_to_pay": "POST workflow JSON; on 402 retry with PAYMENT-SIGNATURE (or legacy X-PAYMENT) header",
    }

# ---------------------------------------------------------------- Protected scan endpoint
def _run_scan(workflow: dict, source: str) -> dict:
    findings = fs_scanner.scan_workflow(workflow, source)
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info")
        summary[sev] = summary.get(sev, 0) + 1
    verdict = "critical" if summary["critical"] else \
              "high" if summary["high"] else \
              "medium" if summary["medium"] else \
              "low" if summary["low"] else "clean"
    return {
        "service": SVC, "flowsentry_version": FS_VERSION,
        "scan": {"source": source, "rules_total": 18,
                 "findings_total": len(findings), "summary": summary,
                 "verdict": verdict},
        "findings": findings,
        "next_steps": "Fix findings by severity; re-scan after changes. "
                      "SARIF/HTML variants: flowsentry CLI (pypi flowsentry).",
    }

@app.post("/v1/scan")
async def scan(request: Request):
    if not fs_scanner:
        return JSONResponse({"error": "scanner unavailable", "detail": _IMPORT_ERR},
                            status_code=503)
    body = await request.body()
    if len(body) > MAX_BODY_BYTES:
        return JSONResponse({"error": "workflow JSON too large (max 2 MB)"}, status_code=413)
    try:
        data = json.loads(body)
    except Exception as exc:
        return JSONResponse({"error": f"body is not valid JSON: {exc}"}, status_code=400)
    if isinstance(data, dict) and isinstance(data.get("workflow"), dict):
        data, srcname = data["workflow"], data.get("name") or "uploaded-workflow"
    elif isinstance(data, dict) and "nodes" in data:
        srcname = data.get("name") or "uploaded-workflow"
    else:
        return JSONResponse(
            {"error": "expected n8n workflow JSON ({'nodes': [...], ...}) or {'name':..., 'workflow': {...}}"},
            status_code=400)
    report = _run_scan(data, str(srcname)[:200])
    # the x402 middleware wraps this route; when paid, our JSON rides with a
    # PAYMENT-RESPONSE header set by the middleware
    return report

# ---------------------------------------------------------------- x402 middleware
facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=FACILITATOR_URL))
resource_server = x402ResourceServer(facilitator)
resource_server.register(NETWORK, ExactEvmServerScheme())
register_bazaar_extension(resource_server)  # catalog paid calls into the Bazaar

routes = {
    "POST /v1/scan": RouteConfig(
        accepts=[PaymentOption(scheme="exact", pay_to=OWNER_ADDR,
                               price=PRICE_USD, network=NETWORK)],
        description="FlowSentry security scan of one n8n workflow JSON export (18 rules, JSON report)",
        mime_type="application/json",
        service_name="flowsentry",
        tags=["security", "n8n", "scanner", "devsecops", "owasp"],
        extensions={"bazaar": BAZAAR_DECLARATION},
    ),
}

app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=resource_server)

# ---------------------------------------------------------------- MCP mount
if mcp_app is not None:
    app.mount("", mcp_app)  # root mount; FastMCP handles exactly /mcp
    # required: MCP session manager lifespan (fastmcp + FastAPI integration)
    app.router.lifespan_context = mcp_app.router.lifespan_context

# vercel serverless entrypoint
app_handler = app
