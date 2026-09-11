#!/usr/bin/env python3
"""Recover Frantic operator identity via desk sign-in link (email flow)."""
import json
import urllib.request
import urllib.error

with open("/home/mihai/secrets/frantic_agent.json") as f:
    d = json.load(f)
op_id = None
# status file has agent info; try to find operator id there
st = json.load(open("/home/mihai/secrets/frantic_agent_status.json"))
agent = st.get("agent", {})
print("agent keys:", list(agent.keys())[:20])
print("kid:", agent.get("kid") or agent.get("agent_kid"))

# request desk sign-in link (operator email = admin@updatesbyai.com)
req = urllib.request.Request(
    "https://gofrantic.com/v1/desk/signin",
    data=json.dumps({"contact": "admin@updatesbyai.com"}).encode(),
    headers={"Content-Type": "application/json", "User-Agent": "vasilica-agent/0.1"},
    method="POST")
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print("desk signin:", r.status, r.read().decode()[:200])
except urllib.error.HTTPError as e:
    print("desk signin HTTP", e.code)
    print(e.read().decode()[:300])