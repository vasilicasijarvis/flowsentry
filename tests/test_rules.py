"""Tests: each rule fires on a crafted vulnerable workflow and not on a clean one."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flowsentry.rules import (  # noqa: E402
    rule_webhook_no_auth, rule_hardcoded_secret_params, rule_hardcoded_secret_http,
    rule_ssrf_metadata, rule_execute_command, rule_code_node, rule_dynamic_code,
    rule_credential_overscoping, rule_expression_command_injection, rule_error_handling,
    rule_sql_injection, rule_plain_http, rule_exposed_trigger, rule_credential_reuse,
    rule_community_nodes, rule_data_exfil, rule_webhook_response, rule_set_secrets,
)


def wf(nodes, name="test-wf", settings=None):
    return {"name": name, "nodes": nodes, "settings": settings or {}}


def node(ntype, name, params=None, creds=None):
    n = {"type": ntype, "name": name, "parameters": params or {}}
    if creds:
        n["credentials"] = creds
    return n


# ---------------- FS001 webhook no auth ----------------

def test_fs001_fires_on_unauth_webhook():
    f = rule_webhook_no_auth(wf([node("n8n-nodes-base.webhook", "Hook")]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS001"


def test_fs001_clean_when_header_auth():
    assert rule_webhook_no_auth(wf([node("n8n-nodes-base.webhook", "Hook",
        {"authentication": "headerAuth"})])) == []


# ---------------- FS002 hardcoded secret in params ----------------

def test_fs002_fires_on_secret_param():
    f = rule_hardcoded_secret_params(wf([node("n8n-nodes-base.slack", "S",
        {"accessToken": "xoxb-1234567890"})]))
    assert any(x["rule_id"] == "FS002" for x in f)


def test_fs002_ignores_expressions():
    f = rule_hardcoded_secret_params(wf([node("n8n-nodes-base.slack", "S",
        {"accessToken": "{{$json.token}}"})]))
    assert not any(x["rule_id"] == "FS002" for x in f)


# ---------------- FS003 HTTP header secret ----------------

def test_fs003_fires_on_literal_auth_header():
    nodes = [node("n8n-nodes-base.httpRequest", "API", {
        "headerParameters": {"parameters": [
            {"name": "Authorization", "value": "Bearer abc123secret"},
        ]},
    })]
    f = rule_hardcoded_secret_http(wf(nodes))
    assert len(f) == 1 and f[0]["rule_id"] == "FS003"


def test_fs003_clean_when_expression():
    nodes = [node("n8n-nodes-base.httpRequest", "API", {
        "headerParameters": {"parameters": [
            {"name": "Authorization", "value": "={{$credentials.x}}"},
        ]},
    })]
    assert rule_hardcoded_secret_http(wf(nodes)) == []


# ---------------- FS004 SSRF metadata ----------------

def test_fs004_fires_on_imds_url():
    f = rule_ssrf_metadata(wf([node("n8n-nodes-base.httpRequest", "Fetch",
        {"url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"})]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS004"


def test_fs004_fires_in_code():
    f = rule_ssrf_metadata(wf([node("n8n-nodes-base.code", "C",
        {"jsCode": "const r = await fetch('http://169.254.169.254/latest/meta-data/');"})]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS004"


# ---------------- FS005 execute command ----------------

def test_fs005_fires_on_execute_command():
    f = rule_execute_command(wf([node("n8n-nodes-base.executeCommand", "Shell",
        {"command": "ls -la /tmp"})]))
    assert len(f) == 1 and f[0]["severity"] == "critical"


# ---------------- FS006 code node ----------------

def test_fs006_fires_on_code_node():
    f = rule_code_node(wf([node("n8n-nodes-base.code", "JS")]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS006"


# ---------------- FS007 dynamic code ----------------

def test_fs007_fires_on_eval():
    f = rule_dynamic_code(wf([node("n8n-nodes-base.code", "C",
        {"jsCode": "const out = eval($json.input);"})]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS007"


def test_fs007_fires_on_python_os_import():
    f = rule_dynamic_code(wf([node("n8n-nodes-base.code", "C",
        {"jsCode": "import os\nos.system($json.cmd)"})]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS007"


def test_fs007_clean_on_plain_code():
    f = rule_dynamic_code(wf([node("n8n-nodes-base.code", "C",
        {"jsCode": "return items.map(i => i.json);"})]))
    assert f == []


# ---------------- FS008 credential overscoping ----------------

def test_fs008_fires_on_admin_cred_name():
    f = rule_credential_overscoping(wf([node("n8n-nodes-base.httpRequest", "API", {},
        {"Admin - all scopes": {"id": "1"}})]))
    assert any(x["rule_id"] == "FS008" for x in f)


# ---------------- FS009 expression command injection ----------------

def test_fs009_fires_on_json_interpolated_command():
    f = rule_expression_command_injection(wf([node("n8n-nodes-base.executeCommand", "Shell",
        {"command": "echo {{$json.filename}}"})]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS009"


# ---------------- FS010 error handling ----------------

def test_fs010_fires_without_error_settings():
    f = rule_error_handling(wf([node("n8n-nodes-base.webhook", "H")]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS010"


def test_fs010_clean_with_error_workflow():
    f = rule_error_handling(wf([node("n8n-nodes-base.webhook", "H")],
        settings={"errorWorkflow": "wf123"}))
    assert f == []


# ---------------- FS011 SQL injection ----------------

def test_fs011_fires_on_interpolated_sql():
    f = rule_sql_injection(wf([node("n8n-nodes-base.postgres", "DB",
        {"query": "SELECT * FROM users WHERE id = {{$json.user_id}}"})]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS011"


def test_fs011_clean_on_parameterized_hint():
    f = rule_sql_injection(wf([node("n8n-nodes-base.postgres", "DB",
        {"query": "SELECT * FROM users WHERE id = $1"})]))
    assert f == []


# ---------------- FS012 plain http ----------------

def test_fs012_fires_on_http_url():
    f = rule_plain_http(wf([node("n8n-nodes-base.httpRequest", "Call",
        {"url": "http://api.internal.example.com/v1/data"})]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS012"


def test_fs012_clean_on_https():
    f = rule_plain_http(wf([node("n8n-nodes-base.httpRequest", "Call",
        {"url": "https://api.example.com/v1/data"})]))
    assert f == []


# ---------------- FS013 exposed trigger ----------------

def test_fs013_fires_on_form_trigger():
    f = rule_exposed_trigger(wf([node("n8n-nodes-base.formTrigger", "Form")]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS013"


# ---------------- FS014 credential reuse ----------------

def test_fs014_fires_on_reused_credential():
    nodes = [node("n8n-nodes-base.httpRequest", f"Call{i}", {},
                  {"Shared Admin Key": {"id": str(i)}}) for i in range(6)]
    f = rule_credential_reuse(wf(nodes))
    assert len(f) == 1 and f[0]["rule_id"] == "FS014" and "6 nodes" in f[0]["message"]


def test_fs014_clean_on_few_usages():
    nodes = [node("n8n-nodes-base.httpRequest", f"Call{i}", {},
                  {"Some Key": {"id": str(i)}}) for i in range(3)]
    assert rule_credential_reuse(wf(nodes)) == []


# ---------------- FS015 community nodes ----------------

def test_fs015_fires_on_community_node():
    f = rule_community_nodes(wf([node("n8n-community-node.big-tool", "X")]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS015"


def test_fs015_clean_on_official_node():
    assert rule_community_nodes(wf([node("n8n-nodes-base.slack", "S")])) == []


# ---------------- FS016 data exfil sink ----------------

def test_fs016_fires_on_webhook_site():
    f = rule_data_exfil(wf([node("n8n-nodes-base.httpRequest", "Debug",
        {"url": "https://webhook.site/abc-123"})]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS016"


# ---------------- FS017 webhook response ----------------

def test_fs017_fires_on_lastnode_mode():
    f = rule_webhook_response(wf([node("n8n-nodes-base.webhook", "H",
        {"responseMode": "lastNode"})]))
    assert len(f) == 1 and f[0]["rule_id"] == "FS017"


# ---------------- FS018 set node secrets ----------------

def test_fs018_fires_on_literal_secret_field():
    nodes = [node("n8n-nodes-base.set", "Set", {
        "assignments": {"assignments": [
            {"name": "stripeApiKey", "value": "sk_live_1234567890"},
        ]},
    })]
    f = rule_set_secrets(wf(nodes))
    assert len(f) == 1 and f[0]["rule_id"] == "FS018"


def test_fs018_clean_on_expression():
    nodes = [node("n8n-nodes-base.set", "Set", {
        "assignments": {"assignments": [
            {"name": "stripeApiKey", "value": "={{$credentials.stripe.key}}"},
        ]},
    })]
    assert rule_set_secrets(wf(nodes)) == []
