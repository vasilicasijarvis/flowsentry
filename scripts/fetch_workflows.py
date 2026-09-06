#!/usr/bin/env python3
"""Fetch public n8n workflow JSONs from GitHub repos for testing FlowSentry."""

import os
import urllib.request

TARGETS = [
    ("yorrickjansen/n8n-webhook-security", "api-authentication.json", "yorrickjansen_api-authentication.json"),
    ("Finfra/dockers", "n8n/w1.json", "finfra_w1.json"),
    ("santifer/jacobo-workflows", "subagente-citas.json", "santifer_subagente-citas.json"),
    ("Cheffromspace/AI-PR-Assistant", "n8n-workflow.json", "cheffromspace_ai-pr-assistant.json"),
    ("DragonJAR/n8n-workflows-esp", "workflows/00485-library-install.json", "dragonjar_library-install.json"),
    ("n8n-io/test-workflows", "workflows/103.json", "n8nio_test_103.json"),
    ("Wilsonoonn/n8n_nl2sql", "nl2sql.json", "wilsonoonn_nl2sql.json"),
    ("AnaamRasool/WhatsApp-Bot", "AI_Bot.json", "anaamrasool_whatsapp-bot.json"),
    ("ZoeyVid/aida-price-checker", "n8n.json", "zoeyvid_aida-price-checker.json"),
    ("House-of-Data/openwebui-n8n-pipe", "openwebui-n8n-pipe.json", "houseofdata_openwebui-pipe.json"),
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "examples", "real")
os.makedirs(OUT, exist_ok=True)

ok = 0
for repo, path, name in TARGETS:
    url = f"https://raw.githubusercontent.com/{repo}/HEAD/{path}"
    dest = os.path.join(OUT, name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "flowsentry-fetch/0.1"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        with open(dest, "wb") as fh:
            fh.write(data)
        print(f"OK   {name} ({len(data)} bytes)  <- {repo}/{path}")
        ok += 1
    except Exception as exc:
        print(f"FAIL {name}: {exc}  <- {repo}/{path}")
print(f"\n{ok}/{len(TARGETS)} downloaded")
