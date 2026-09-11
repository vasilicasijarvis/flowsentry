#!/usr/bin/env python3
"""Inspect frantic_agent.json top-level keys."""
import json

d = json.load(open("/home/mihai/secrets/frantic_agent.json"))
print(list(d.keys()))
# nested scan for agent_slug
for k, v in d.items():
    if isinstance(v, dict) and "agent_slug" in v:
        print("found in:", k, "|", v.get("agent_slug"))