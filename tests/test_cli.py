#!/usr/bin/env python3
"""CLI integration tests: exit codes, report files, edge cases."""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import unittest  # noqa: E402

from flowsentry.scanner import main  # noqa: E402
from flowsentry import scanner as S  # noqa: E402


def wf_file(tmp, name, payload):
    path = os.path.join(tmp, name)
    with open(path, "w") as fh:
        json.dump(payload, fh)
    return path


VULN_WF = {
    "name": "vuln", "settings": {},
    "nodes": [{"type": "n8n-nodes-base.webhook", "name": "H", "parameters": {}}],
}


class TestExitCodes(unittest.TestCase):
    def test_never_returns_zero_despite_findings(self):
        """Regression: --fail-on never must exit 0 even with findings (CI uses it)."""
        with tempfile.TemporaryDirectory() as tmp:
            path = wf_file(tmp, "v.json", VULN_WF)
            rc = main(["scan", path, "--fail-on", "never"])
        self.assertEqual(rc, 0)

    def test_default_threshold_high_returns_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = wf_file(tmp, "v.json", VULN_WF)
            rc = main(["scan", path])
        self.assertEqual(rc, 1)

    def test_fail_on_medium_returns_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = wf_file(tmp, "v.json", VULN_WF)
            rc = main(["scan", path, "--fail-on", "medium"])
        self.assertEqual(rc, 1)

    def test_clean_workflow_returns_zero(self):
        clean = {
            "name": "clean", "settings": {"errorWorkflow": "x"},
            "nodes": [{"type": "n8n-nodes-base.webhook", "name": "H",
                       "parameters": {"authentication": "headerAuth",
                                      "responseMode": "onReceived"}}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = wf_file(tmp, "c.json", clean)
            rc = main(["scan", path, "--fail-on", "never"])
        self.assertEqual(rc, 0)


class TestReports(unittest.TestCase):
    def test_json_report_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = wf_file(tmp, "v.json", VULN_WF)
            out = os.path.join(tmp, "r.json")
            main(["scan", path, "--json", out, "--fail-on", "never"])
            data = json.load(open(out))
        self.assertEqual(data["summary"]["critical"], 1)
        rule_ids = {f["rule_id"] for f in data["findings"]}
        self.assertIn("FS001", rule_ids)
        self.assertIn("FS010", rule_ids)  # no error handling in VULN_WF

    def test_sarif_valid_and_uploads_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = wf_file(tmp, "v.json", VULN_WF)
            out = os.path.join(tmp, "r.sarif")
            main(["scan", path, "--sarif", out, "--fail-on", "never"])
            sarif = json.load(open(out))
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertEqual(sarif["runs"][0]["tool"]["driver"]["name"], "FlowSentry")
        self.assertTrue(sarif["runs"][0]["results"])

    def test_html_report_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = wf_file(tmp, "v.json", VULN_WF)
            out = os.path.join(tmp, "r.html")
            main(["scan", path, "--html", out, "--fail-on", "never"])
            html = open(out).read()
        self.assertIn("FlowSentry Security Report", html)

    def test_wrapped_export_format_supported(self):
        wrapped = {"workflow": VULN_WF, "meta": {"instanceId": "x"}}
        with tempfile.TemporaryDirectory() as tmp:
            path = wf_file(tmp, "w.json", wrapped)
            rc = main(["scan", path])  # default threshold: wrapped WF has critical finding
        self.assertEqual(rc, 1)


class TestEdgeCases(unittest.TestCase):
    def test_invalid_json_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad.json")
            with open(bad, "w") as fh:
                fh.write("{not json")
            good = wf_file(tmp, "good.json", VULN_WF)
            rc = main(["scan", bad, good])  # default threshold: high -> findings fail
        self.assertEqual(rc, 1)  # good.json still produced findings

    def test_rule_exception_becomes_fserr_not_crash(self):
        broken_wf = {"name": "b", "nodes": [{"type": "n8n-nodes-base.webhook", "name": 123,
                                             "parameters": {}}], "settings": {}}
        findings = S.scan_workflow(broken_wf, "mem")
        # must not raise; may produce findings
        self.assertIsInstance(findings, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
