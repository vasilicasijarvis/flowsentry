#!/usr/bin/env python3
"""Spot-check specific nodes behind critical findings."""

import json
import os

REAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "real")

CHECKS = [
    ("yorrickjansen_api-authentication.json", "API: JWT auth with auth server validation"),
    ("finfra_w1.json", "HTTP Trigger"),
    ("santifer_subagente-citas.json", "Webhook"),
    ("wilsonoonn_nl2sql.json", "Webhook"),
    ("n8nio_test_103.json", "Execute Command"),
    ("dragonjar_library-install.json", "library_install"),
]

for fname, nodename in CHECKS:
    path = os.path.join(REAL, fname)
    data = json.load(open(path))
    if isinstance(data, dict) and isinstance(data.get("workflow"), dict):
        data = data["workflow"]
    for n in data.get("nodes", []):
        if n.get("name") == nodename:
            p = n.get("parameters", {})
            print(f"--- {fname} | {nodename}")
            print(f"    type={n.get('type')} authentication={p.get('authentication')!r}")
            print(f"    param keys: {sorted(p.keys())[:10]}")
            cmd = p.get("command", "")
            if cmd:
                print(f"    command: {cmd[:120]}")
            path_ = p.get("path", "")
            if path_:
                print(f"    webhook path: {path_}")
            print()
