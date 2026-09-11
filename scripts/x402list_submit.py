#!/usr/bin/env python3
"""Submit FlowSentry to x402-list.com with the exact form schema."""
import json
import urllib.parse
import urllib.request
import urllib.error

SUBMIT = "https://x402-list.com/api/v1/submit"
DESC = ("Security scanner for n8n workflow JSON and MCP server configs, sold per-scan over x402. "
        "POST a workflow export, receive findings ranked by severity: webhooks without auth, hardcoded "
        "API keys, SSRF, command injection, 18 rules total. 0.50 USDC per scan on Base (x402 exact, "
        "v2). Free demo scan via X-FlowSentry-Demo header. Open-source CLI on GitHub; listed in the "
        "official MCP Registry.")

payload = {
    "submission_type": "service",
    "service_name": "FlowSentry Workflow Security Scanner",
    "service_url": "https://flowsentry.vercel.app/api/scan",
    "website_url": "https://flowsentry-agentpay.vercel.app",
    "email": "admin@updatesbyai.com",
    "category": "Security" if False else "Verification",
    "description": DESC,
    "endpoints": "/api/scan",
    "notes": "Network: Base (eip155:8453), USDC, scheme exact, x402Version 2. "
             "The endpoint returns HTTP 402 with PAYMENT-REQUIRED headers on unpaid requests; "
             "a valid x402 payment header settles via the x402.org facilitator. Demo header documented.",
}

data = urllib.parse.urlencode(payload).encode()
req = urllib.request.Request(SUBMIT, data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded",
                                      "User-Agent": "Mozilla/5.0"},
                             method="POST")
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print("status:", r.status)
        print(r.read().decode()[:600])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode()[:600])