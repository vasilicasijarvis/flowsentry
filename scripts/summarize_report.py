#!/usr/bin/env python3
"""Summarize scan_report.json into README-ready text."""

import json
from collections import defaultdict

with open("/home/mihai/flowsentry/examples/scan_report.json") as fh:
    report = json.load(fh)

by_rule = defaultdict(list)
by_file = defaultdict(lambda: defaultdict(int))
for f in report["findings"]:
    by_rule[f["rule_id"]].append(f)
    by_file[f["source"]][f["severity"]] += 1

print("=== CRITICAL FINDINGS (rule, node, file) ===")
for f in report["findings"]:
    if f["severity"] == "critical":
        src = f["source"].split("/")[-1]
        print(f"  {f['rule_id']:6} {src:42} {f['node_name'][:38]:38} {f['title'][:48]}")

print("\n=== RULE COVERAGE ON REAL WORKFLOWS ===")
for rid in sorted(by_rule):
    files = sorted({f['source'].split('/')[-1] for f in by_rule[rid]})
    print(f"  {rid}: {len(by_rule[rid])}x in {len(files)} files: {', '.join(files[:5])}")

print("\n=== SEV PER FILE ===")
for src in sorted(by_file):
    sev = by_file[src]
    print(f"  {src.split('/')[-1]:45} c={sev.get('critical',0)} m={sev.get('medium',0)}")
