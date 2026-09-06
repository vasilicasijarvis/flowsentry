#!/usr/bin/env python3
"""FlowSentry - security scanner for n8n workflow JSON exports.

Usage:
  flowsentry scan <files-or-dirs...> [--json OUT.json] [--sarif OUT.sarif] [--html OUT.html]
  flowsentry rules
  flowsentry --version

Exit codes:
  0 - no findings above threshold
  1 - findings found (or --fail-on threshold exceeded)
  2 - usage/IO error
"""

import argparse
import json
import os
import sys
import datetime
from html import escape

from . import __version__
from .rules import ALL_RULES, RULES_META

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

SEV_ICONS = {"critical": "[!]", "high": "[+]", "medium": "[~]", "low": "[-]", "info": "[i]"}
SEV_COLORS = {
    "critical": "\033[1;91m", "high": "\033[91m", "medium": "\033[93m",
    "low": "\033[96m", "info": "\033[97m", "reset": "\033[0m", "bold": "\033[1m",
}


def use_color():
    return sys.stdout.isatty() or os.environ.get("FORCE_COLOR") == "1"


def load_workflow(path):
    """Load one workflow JSON file. Returns (workflow_dict, error)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, f"not valid JSON: {exc}"
    except OSError as exc:
        return None, f"cannot read: {exc}"
    if isinstance(data, dict) and isinstance(data.get("workflow"), dict):
        # n8n CLI export format wraps in {"workflow": {...}}
        data = data["workflow"]
    if not isinstance(data, dict) or "nodes" not in data:
        return None, "no 'nodes' key - is this an n8n workflow export?"
    return data, None


def collect_files(inputs):
    """Expand files/directories into a list of .json workflow files."""
    files = []
    for item in inputs:
        if os.path.isdir(item):
            for root, _dirs, names in os.walk(item):
                for name in sorted(names):
                    if name.endswith(".json"):
                        files.append(os.path.join(root, name))
        elif os.path.isfile(item):
            files.append(item)
        else:
            print(f"warning: path not found: {item}", file=sys.stderr)
    return files


def scan_workflow(wf, source):
    """Run all rules against one workflow dict. Returns list of findings."""
    findings = []
    for rule_fn in ALL_RULES:
        try:
            findings.extend(rule_fn(wf))
        except Exception as exc:  # a rule must never kill the scan
            findings.append({
                "rule_id": "FSERR",
                "severity": "info",
                "title": "Rule error",
                "node_name": "-",
                "node_type": "-",
                "message": f"rule {rule_fn.__name__} failed on this workflow: {exc}",
                "remediation": "Report this at https://github.com/vasilicasijarvis/flowsentry/issues",
            })
    for f in findings:
        f["source"] = source
        f["workflow"] = wf.get("name", os.path.basename(source))
        f["owasp"] = RULES_META.get(f["rule_id"], ("?", "?", "-"))[2]
    return findings


def sort_key(f):
    return (-SEVERITY_ORDER.get(f.get("severity", "info"), 0), f.get("source", ""), f.get("rule_id", ""))


def summary_counts(findings):
    counts = {s: 0 for s in ("critical", "high", "medium", "low", "info")}
    for f in findings:
        counts[f.get("severity", "info")] = counts.get(f.get("severity", "info"), 0) + 1
    return counts


def print_report(findings, files_scanned, rule_errors):
    color = use_color()
    c = SEV_COLORS if color else {k: "" for k in SEV_COLORS}

    print()
    print(f"{c['bold']}  +----------------------------------------------------+")
    print(f"  |   FlowSentry v{__version__}  -  n8n security scan        |")
    print(f"  +----------------------------------------------------+{c['reset']}")
    print()
    print(f"  Scanned: {files_scanned} workflow file(s)")
    if rule_errors:
        print(f"  {c['medium']}Note: {rule_errors} rule error(s) suppressed - see FSERR findings.{c['reset']}")
    print()

    by_source = {}
    for f in findings:
        by_source.setdefault(f["source"], []).append(f)

    for source in sorted(by_source):
        src_findings = sorted(by_source[source], key=sort_key)
        wf_name = src_findings[0].get("workflow", source)
        counts = summary_counts(src_findings)
        verdict = "CLEAN" if not src_findings else f"{len(src_findings)} finding(s)"
        print(f"  {c['bold']}{source}{c['reset']}  ({wf_name}) - {verdict}")
        for f in src_findings:
            sev = f["severity"]
            icon = SEV_ICONS.get(sev, "[?]")
            print(f"    {c.get(sev, '')}{icon} {sev.upper():<8}{c['reset']} "
                  f"{f['rule_id']} {f['title']}")
            print(f"           node: {f['node_name']}  ({f['node_type']})")
            print(f"           {f['message']}")
            print(f"           fix: {f['remediation']}")
            if f.get("evidence"):
                print(f"           evidence: {f['evidence']}")
            print()

    total = summary_counts(findings)
    print(f"  {c['bold']}Summary{c['reset']}")
    print(f"    critical: {total['critical']}   high: {total['high']}   "
          f"medium: {total['medium']}   low: {total['low']}")
    if total["critical"] or total["high"]:
        print(f"  {c['critical']}{c['bold']}  Result: FAIL - fix critical/high findings before production.{c['reset']}")
    elif findings:
        print(f"  {c['medium']}  Result: PASS with warnings.{c['reset']}")
    else:
        print(f"  {c['low']}  Result: PASS - no findings.{c['reset']}")
    print()


def write_json_report(findings, path, files_scanned):
    payload = {
        "tool": "flowsentry",
        "version": __version__,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "files_scanned": files_scanned,
        "summary": summary_counts(findings),
        "findings": findings,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def write_sarif_report(findings, path):
    rules_seen = sorted({f["rule_id"] for f in findings if f["rule_id"] != "FSERR"})
    sarif_rules = []
    for rid in rules_seen:
        meta = RULES_META.get(rid, (rid, "info", "-"))
        sarif_rules.append({
            "id": rid,
            "name": meta[0].replace(" ", ""),
            "shortDescription": {"text": meta[0]},
            "fullDescription": {"text": meta[0]},
            "help": {"text": f"OWASP Agentic mapping: {meta[2]}"},
            "defaultConfiguration": {"level": {"critical": "error", "high": "error",
                                               "medium": "warning", "low": "note"}.get(meta[1], "note")},
        })
    level_map = {"critical": "error", "high": "error", "medium": "warning",
                 "low": "note", "info": "note"}
    results = []
    for f in findings:
        if f["rule_id"] == "FSERR":
            continue
        results.append({
            "ruleId": f["rule_id"],
            "level": level_map.get(f["severity"], "note"),
            "message": {"text": f"{f['title']}: {f['message']} Fix: {f['remediation']}"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f["source"]},
                    "region": {"startLine": 1},
                },
                "logicalLocations": [{"name": f["node_name"]}],
            }],
        })
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "FlowSentry", "version": __version__,
                                "informationUri": "https://github.com/vasilicasijarvis/flowsentry",
                                "rules": sarif_rules}},
            "results": results,
        }],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(sarif, fh, indent=2)


def write_html_report(findings, path, files_scanned):
    rows = []
    for f in sorted(findings, key=sort_key):
        ev = f"<code>{escape(str(f['evidence']))}</code>" if f.get("evidence") else ""
        rows.append(f"""
        <tr class="{f['severity']}">
          <td><span class="pill">{f['severity']}</span></td>
          <td>{f['rule_id']}</td>
          <td>{escape(f['source'])}</td>
          <td>{escape(f['node_name'])}<br><small>{escape(f['node_type'])}</small></td>
          <td><b>{escape(f['title'])}</b><br>{escape(f['message'])}<br>
              <small>Fix: {escape(f['remediation'])}</small>{ev}</td>
          <td><small>{escape(str(f['owasp']))}</small></td>
        </tr>""")
    total = summary_counts(findings)
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>FlowSentry Report</title>
<style>
body{{font-family:ui-sans-serif,system-ui,sans-serif;background:#0a0e1a;color:#e2e8f0;margin:0;padding:40px}}
h1{{background:linear-gradient(135deg,#22d3ee,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
table{{border-collapse:collapse;width:100%;margin-top:24px}}
td,th{{border:1px solid #1f2937;padding:10px;text-align:left;vertical-align:top;font-size:14px}}
th{{background:#111827}}
.pill{{padding:2px 10px;border-radius:999px;font-size:12px;font-weight:700}}
tr.critical .pill{{background:#7f1d1d;color:#fecaca}}
tr.high .pill{{background:#7c2d12;color:#fed7aa}}
tr.medium .pill{{background:#713f12;color:#fef08a}}
tr.low .pill{{background:#164e63;color:#a5f3fc}}
code{{background:#111827;padding:2px 6px;border-radius:4px;display:inline-block;margin-top:6px;font-size:12px}}
.sum{{margin-top:12px;color:#94a3b8}}
</style></head><body>
<h1>FlowSentry Security Report</h1>
<p class="sum">Generated {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} -
{files_scanned} file(s) scanned - {len(findings)} finding(s)
(critical: {total['critical']}, high: {total['high']}, medium: {total['medium']}, low: {total['low']})</p>
<table><tr><th>Severity</th><th>Rule</th><th>File</th><th>Node</th><th>Detail</th><th>OWASP Agentic</th></tr>
{''.join(rows)}
</table>
<p class="sum">FlowSentry v{__version__} - github.com/vasilicasijarvis/flowsentry</p>
</body></html>"""
    with open(path, "w", encoding="utf-8") as fh:
        html_all = html
        fh.write(html_all)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="flowsentry",
        description="FlowSentry - security scanner for n8n workflow JSON exports.",
    )
    parser.add_argument("--version", action="version", version=f"flowsentry {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_scan = sub.add_parser("scan", help="scan workflow JSON files or directories")
    p_scan.add_argument("inputs", nargs="+", help="files or directories to scan")
    p_scan.add_argument("--json", dest="json_out", help="write JSON report to file")
    p_scan.add_argument("--sarif", dest="sarif_out", help="write SARIF 2.1.0 report to file")
    p_scan.add_argument("--html", dest="html_out", help="write HTML report to file")
    p_scan.add_argument("--fail-on", dest="fail_on", default="high",
                        choices=["critical", "high", "medium", "low", "never"],
                        help="exit 1 if findings at/above this severity exist (default: high)")

    sub.add_parser("rules", help="list all rules")

    args = parser.parse_args(argv)

    if args.command == "rules":
        print(f"FlowSentry v{__version__} - {len(ALL_RULES)} rules\n")
        for rid in sorted(RULES_META):
            title, sev, owasp = RULES_META[rid]
            print(f"  {rid}  {sev.upper():<8} {title}  [{owasp}]")
        return 0

    if args.command != "scan":
        parser.print_help()
        return 2

    files = collect_files(args.inputs)
    if not files:
        print("error: no JSON files found to scan", file=sys.stderr)
        return 2

    all_findings = []
    rule_errors = 0
    scanned = 0
    for path in files:
        wf, err = load_workflow(path)
        if wf is None:
            print(f"  skipping {path}: {err}", file=sys.stderr)
            continue
        scanned += 1
        before = len(all_findings)
        all_findings.extend(scan_workflow(wf, path))
        rule_errors += sum(1 for f in all_findings[before:] if f["rule_id"] == "FSERR")

    print_report(all_findings, scanned, rule_errors)

    if args.json_out:
        write_json_report(all_findings, args.json_out, scanned)
        print(f"  JSON report: {args.json_out}")
    if args.sarif_out:
        write_sarif_report(all_findings, args.sarif_out)
        print(f"  SARIF report: {args.sarif_out}")
    if args.html_out:
        write_html_report(all_findings, args.html_out, scanned)
        print(f"  HTML report: {args.html_out}")

    total = summary_counts(all_findings)
    threshold = SEVERITY_ORDER[args.fail_on] if args.fail_on != "never" else 0
    breached = sum(v for k, v in total.items() if SEVERITY_ORDER.get(k, 0) >= threshold and k != "info")
    return 1 if breached else 0


if __name__ == "__main__":
    sys.exit(main())
