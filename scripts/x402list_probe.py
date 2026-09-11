#!/usr/bin/env python3
"""Probe x402-list submit schema variants."""
import json
import urllib.request
import urllib.error

SUBMIT = "https://x402-list.com/api/v1/submit"
EMAIL = "admin@updatesbyai.com"
DESC = ("Paid security scan for n8n workflow JSON and MCP server configs. POST a workflow export, "
        "get findings ranked by severity (webhooks without auth, hardcoded API keys, SSRF, command "
        "injection, 18 rules). $0.50 USDC per scan on Base. Free demo scan via X-FlowSentry-Demo: 1.")

BASE = {"email": EMAIL, "service_name": "FlowSentry Workflow Security Scanner", "description": DESC}

variants = [
    ("url only", {**BASE, "url": "https://flowsentry.vercel.app/api/scan"}),
    ("site+endpoint str", {**BASE, "url": "https://flowsentry.vercel.app", "endpoint": "/api/scan"}),
    ("urls list", {**BASE, "urls": ["https://flowsentry.vercel.app/api/scan"]}),
    ("website field", {**BASE, "website": "https://flowsentry.vercel.app/api/scan"}),
    ("full https url bare", {**BASE, "url": "https://flowsentry.vercel.app/api/scan", "network": "base"}),
    ("url+website+cat+paths", {**BASE,
                               "url": "https://flowsentry.vercel.app/api/scan",
                               "website": "https://flowsentry.vercel.app",
                               "category": "security",
                               "endpoint_paths": ["/api/scan"]}),
    ("url+cat+endpoints arr", {**BASE,
                               "url": "https://flowsentry.vercel.app/api/scan",
                               "category": "security",
                               "endpoints": [{"path": "/api/scan", "method": "POST"}]}),
    ("websites v1", {**BASE, "url": "https://flowsentry.vercel.app/api/scan",
                     "category": "security", "endpoints": [{"path": "/api/scan", "method": "POST"}],
                     "website": "https://flowsentry.vercel.app/"}),
    ("websites v2 github", {**BASE, "url": "https://flowsentry.vercel.app/api/scan",
                            "category": "security", "endpoints": [{"path": "/api/scan", "method": "POST"}],
                            "website": "https://github.com/vasilicasijarvis/flowsentry"}),
    ("websites v3 agentpay", {**BASE, "url": "https://flowsentry.vercel.app/api/scan",
                              "category": "security", "endpoints": [{"path": "/api/scan", "method": "POST"}],
                              "website": "https://flowsentry-agentpay.vercel.app"}),
]

for name, payload in variants:
    req = urllib.request.Request(SUBMIT, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            print(f"{name}: {r.status} {r.read().decode()[:300]}")
            break
    except urllib.error.HTTPError as e:
        print(f"{name}: HTTP {e.code} {e.read().decode()[:200]}")