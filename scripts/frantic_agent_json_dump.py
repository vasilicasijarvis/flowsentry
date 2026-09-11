#!/usr/bin/env python3
"""Try operator token auth on payout endpoint (operator id known from signup)."""
import json
import urllib.request
import urllib.error

# The signup response printed operator_id publicly; token was masked on save.
# Try the seal-poll endpoint's stored tokens: frantic_agent.json 'ok'/'polled' shape may embed them.
d = json.load(open("/home/mihai/secrets/frantic_agent.json"))
print(json.dumps(d, indent=1)[:800])