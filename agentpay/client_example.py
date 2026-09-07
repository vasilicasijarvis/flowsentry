#!/usr/bin/env python3
"""
Example: how an AI agent pays FlowSentry over x402 (USDC on Base Sepolia).

Two-step protocol, zero accounts:
  1. POST the workflow -> 402 + PAYMENT-REQUIRED header (payment terms)
  2. Sign + settle via the x402 facilitator, retry with PAYMENT-SIGNATURE header
     -> 200 + JSON report + PAYMENT-RESPONSE (settlement receipt)

Requirements on the AGENT's machine:
    pip install "x402[evm]" eth-account
Fund your agent wallet with Base Sepolia USDC + ETH for gas:
    https://faucet.circle.com  (USDC)  +  https://faucet.quicknode.com/base/sepolia (ETH)
"""
import base64
import json

from eth_account import Account
from x402 import x402Client
from x402.mechanisms.evm.exact import ExactEvmScheme
from x402.http import HTTPFacilitatorClient, FacilitatorConfig

URL = "https://flowsentry-agentpay.vercel.app/v1/scan"
WORKFLOW = {
    "name": "my-workflow",
    "nodes": [
        {"name": "Webhook", "type": "n8n-nodes-base.webhook",
         "parameters": {"path": "ingest", "authentication": "none"}},
        {"name": "Exec", "type": "n8n-nodes-base.executeCommand",
         "parameters": {"command": "curl http://169.254.169.254/latest/meta-data/"}},
    ],
    "connections": {},
}

PRIVATE_KEY = "0x..."  # agent wallet key (NOT FlowSentry's receiver key)

client = x402Client()
client.register("eip155:84532", ExactEvmScheme(Account.from_key(PRIVATE_KEY)))

import httpx

# step 1: probe
r = httpx.post(URL, json=WORKFLOW)
if r.status_code != 402:
    print(json.dumps(r.json(), indent=1)[:600])
    raise SystemExit

terms_b64 = r.headers["PAYMENT-REQUIRED"]
terms = json.loads(base64.b64decode(terms_b64))
print("price:", terms["accepts"][0]["amount"], "atomic USDC | payTo:", terms["accepts"][0]["payTo"])

# step 2: sign payment and retry (x402 SDK builds PAYMENT-SIGNATURE from terms)
payment_payload = client.create_payment_payload(terms)  # dict, x402 v2 schema
r2 = httpx.post(URL, json=WORKFLOW,
                headers={"PAYMENT-SIGNATURE": base64.b64encode(
                    json.dumps(payment_payload).encode()).decode()})
print("status:", r2.status_code)
report = r2.json()
print("verdict:", report["scan"]["verdict"], "| findings:", report["scan"]["findings_total"])
receipt_b64 = r2.headers.get("PAYMENT-RESPONSE")
if receipt_b64:
    print("settlement receipt:", json.loads(base64.b64decode(receipt_b64)))
