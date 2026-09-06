"""FlowSentry security rules for n8n workflow JSON exports.

Each rule function takes a workflow dict and yields finding dicts with:
  rule_id, severity, title, node_name, node_type, message, remediation

Rule metadata (OWASP Agentic Top 10 mapping) lives in RULES_META.
"""

import re

# Map rule_id -> (title, severity, owasp_agentic_mapping)
RULES_META = {
    "FS001": ("Webhook endpoint without authentication", "critical", "A01 Agent Identity Abuse"),
    "FS002": ("Hardcoded secret in node parameters", "critical", "A02 Excessive Agency / Secrets"),
    "FS003": ("Hardcoded secret in HTTP header/query", "high", "A02 Excessive Agency / Secrets"),
    "FS004": ("SSRF / cloud metadata endpoint access", "critical", "A05 Confused Deputy"),
    "FS005": ("Execute Command node without guardrails", "critical", "A03 Shell Injection"),
    "FS006": ("Code node without sandbox hardening", "medium", "A03 Code Injection"),
    "FS007": ("Dynamic code construction in Code node (eval-style)", "critical", "A03 Code Injection"),
    "FS008": ("Credential over-scoping / unusual credential type", "medium", "A02 Excessive Agency"),
    "FS009": ("Expression-based command injection", "critical", "A03 Shell Injection"),
    "FS010": ("Missing error handling on workflow", "medium", "A06 Memory & Data Exposure"),
    "FS011": ("Raw SQL query construction from expressions", "high", "A03 Injection"),
    "FS012": ("HTTP node without TLS (plain http://)", "high", "A04 Bag of Tools"),
    "FS013": ("Trigger node exposed without auth", "medium", "A01 Agent Identity Abuse"),
    "FS014": ("Credential reuse across many nodes", "medium", "A02 Excessive Agency"),
    "FS015": ("Unknown/external community node without review", "medium", "A04 Bag of Tools"),
    "FS016": ("Sensitive data sent to external sink", "medium", "A06 Memory & Data Exposure"),
    "FS017": ("Webhook response mode exposes internals", "medium", "A06 Memory & Data Exposure"),
    "FS018": ("Set node storing secrets in plaintext", "medium", "A02 Excessive Agency"),
}

# Known cloud metadata endpoints (AWS/Azure/GCP/Alibaba)
_METADATA_PATTERNS = [
    "169.254.169.254",
    "metadata.google.internal",
    "100.100.100.200",
]

_SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|apikey|secret|token|password|passwd|pwd|authorization|bearer|private[_-]?key)",
    re.I,
)

_ASSIGN_SECRET_RE = re.compile(
    r"""(?:const|let|var)\s+\w*(secret|token|password|apikey|api_key|credential)\w*\s*=\s*['"][^'"]{4,}['"]""",
    re.I,
)

_TEMPLATE_ASSIGN_SECRET_RE = re.compile(
    r"""(?:secret|token|password|apikey|api_key)\s*[:=]\s*['"][^'"\s]{6,}['"]""",
    re.I,
)

_SQL_PATTERN = re.compile(
    r"(SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM)",
    re.I,
)

_EXPRESSION_RE = re.compile(r"\{\{.*?\}\}", re.S)


def _iter_nodes(wf):
    for node in wf.get("nodes", []):
        if isinstance(node, dict):
            yield node


def _node_param(node, key, default=""):
    val = node.get("parameters", {}).get(key, default)
    return val if isinstance(val, str) else default


def _finding(rule_id, node, message, remediation, severity=None, evidence=None):
    f = {
        "rule_id": rule_id,
        "severity": severity or RULES_META[rule_id][1],
        "title": RULES_META[rule_id][0],
        "node_name": node.get("name", "?"),
        "node_type": node.get("type", "?"),
        "message": message,
        "remediation": remediation,
    }
    if evidence:
        f["evidence"] = evidence
    return f


def rule_webhook_no_auth(wf):
    """FS001 - Webhook nodes with authentication set to none."""
    findings = []
    for node in _iter_nodes(wf):
        if node.get("type") != "n8n-nodes-base.webhook":
            continue
        params = node.get("parameters", {})
        auth = params.get("authentication", "none")
        if not auth or str(auth).lower() in ("none", ""):
            findings.append(_finding(
                "FS001", node,
                "Webhook node has authentication set to 'none'. Anyone who can reach the "
                "n8n instance can trigger this workflow and its downstream actions.",
                "Set Webhook > Authentication to Basic/Header/JWT auth, or validate a "
                "shared-secret header in the workflow before doing anything sensitive.",
            ))
    return findings


def rule_hardcoded_secret_params(wf):
    """FS002 - Hardcoded secrets in any node parameter values."""
    findings = []
    for node in _iter_nodes(wf):
        params = node.get("parameters", {})
        for key, value in params.items():
            if not isinstance(value, str):
                continue
            if "{{" in value:
                continue  # expression, resolved at runtime from credentials
            if _SECRET_KEY_RE.search(key) and len(value) >= 6:
                findings.append(_finding(
                    "FS002", node,
                    f"Parameter '{key}' looks like it contains a hardcoded secret "
                    f"(literal value, no expression). Exports of workflows frequently leak like this.",
                    "Move the value into an n8n credential and reference it via expressions.",
                    evidence=f"{key}={value[:4]}***",
                ))
    return findings


def rule_hardcoded_secret_http(wf):
    """FS003 - Hardcoded secrets in HTTP node headers / query parameters."""
    findings = []
    for node in _iter_nodes(wf):
        if node.get("type") != "n8n-nodes-base.httpRequest":
            continue
        params = node.get("parameters", {})
        for group_key in ("headerParameters", "queryParameters"):
            group = params.get(group_key, {})
            for item in group.get("parameters", []):
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", ""))
                value = str(item.get("value", ""))
                if _SECRET_KEY_RE.search(name) and value and "{{" not in value:
                    findings.append(_finding(
                        "FS003", node,
                        f"HTTP node sends hardcoded secret in {group_key}: '{name}' "
                        "(literal value, not resolved from a credential).",
                        "Use an n8n credential (e.g. Header Auth) instead of a literal secret.",
                        evidence=f"{name}: {value[:4]}***",
                    ))
    return findings


def rule_ssrf_metadata(wf):
    """FS004 - SSRF / cloud metadata endpoints targeted from HTTP or Code nodes."""
    findings = []
    for node in _iter_nodes(wf):
        ntype = node.get("type", "")
        blobs = []
        if ntype == "n8n-nodes-base.httpRequest":
            url = _node_param(node, "url")
            blobs.append(("url", url))
        elif ntype in ("n8n-nodes-base.code", "n8n-nodes-base.function",
                       "n8n-nodes-base.functionItem"):
            code = _node_param(node, "jsCode") or _node_param(node, "functionCode")
            blobs.append(("code", code))
        for field, blob in blobs:
            for md in _METADATA_PATTERNS:
                if md in blob:
                    findings.append(_finding(
                        "FS004", node,
                        f"Node references cloud metadata endpoint '{md}' in {field}. "
                        "If workflow inputs can influence this URL, an attacker can pivot "
                        "to instance credentials (SSRF/IMDS).",
                        "Remove metadata endpoint access; if required, pin the exact path, "
                        "blocklist metadata IPs in egress, and never interpolate user input "
                        "into the URL.",
                        evidence=md,
                    ))
    return findings


def rule_execute_command(wf):
    """FS005 - Execute Command nodes: arbitrary shell by design."""
    findings = []
    for node in _iter_nodes(wf):
        if node.get("type") != "n8n-nodes-base.executeCommand":
            continue
        cmd = _node_param(node, "command")
        dynamic = bool(_EXPRESSION_RE.search(cmd))
        findings.append(_finding(
            "FS005", node,
            ("Execute Command node runs an expression-built command ({{...}}) - "
             "workflow data flows into a shell."
             if dynamic else
             "Execute Command node runs shell commands with the n8n process privileges. "
             "Combined with an unauthenticated trigger this is remote code execution."),
            "Replace with dedicated nodes, pin an exact static command, run n8n in a "
            "restricted container, and require authenticated triggers upstream.",
            severity="critical",
            evidence=(cmd[:80] if cmd else None),
        ))
    return findings


def rule_code_node(wf):
    """FS006 - Code nodes (Python/JS) run with n8n privileges; flag presence + mode."""
    findings = []
    risky_types = ("n8n-nodes-base.code", "n8n-nodes-base.function", "n8n-nodes-base.functionItem")
    for node in _iter_nodes(wf):
        if node.get("type") not in risky_types:
            continue
        mode = node.get("parameters", {}).get("mode", "runOnceForAllItems")
        findings.append(_finding(
            "FS006", node,
            f"Code node present (mode={mode}). Custom code runs inside n8n; in 'runOnceForAllItems' "
            "JS mode with task runners disabled it can reach the host environment.",
            "Enable N8N_RUNNERS_ENABLED=true (task runners sandbox), keep code reviewed in "
            "version control, and avoid importing os/child_process.",
        ))
    return findings


def rule_dynamic_code(wf):
    """FS007 - Code nodes that build code from strings (eval/new Function/indirect access)."""
    findings = []
    risky_types = ("n8n-nodes-base.code", "n8n-nodes-base.function", "n8n-nodes-base.functionItem")
    patterns = [
        (r"\beval\s*\(", "eval()"),
        (r"new\s+Function\s*\(", "new Function()"),
        (r"require\s*\(\s*['\"]child_process", "child_process import"),
        (r"import\s+os\b|require\s*\(\s*['\"]os['\"]", "os module import"),
        (r"subprocess|os\.system|os\.popen", "subprocess/os.system"),
        (r"\$\(\s*[^'\"]", "dynamic node access $(<expression>)"),
    ]
    for node in _iter_nodes(wf):
        if node.get("type") not in risky_types:
            continue
        code = _node_param(node, "jsCode") or _node_param(node, "functionCode")
        for pat, label in patterns:
            if pat in code or re.search(pat, code):
                findings.append(_finding(
                    "FS007", node,
                    f"Code node uses {label} - string-built logic or host access, a classic "
                    "expression/code injection sink when workflow data reaches it.",
                    "Remove dynamic evaluation; if unavoidable, strictly allowlist inputs "
                    "and run the workflow in an isolated worker.",
                    severity="critical",
                    evidence=label,
                ))
                break
    return findings


_OVERSCOPED_HINTS = (
    "admin", "root", "owner", "all-scopes", "full", "wildcard", "*",
)


def rule_credential_overscoping(wf):
    """FS008 - Credentials whose names hint at broad scope, or unusual/unknown types."""
    findings = []
    known_prefixes = (
        "n8n-nodes-base", "n8n-nodes-langchain", "n8n-nodes-httpRequest", "httpBasicAuth",
    )
    counts = {}
    for node in _iter_nodes(wf):
        creds = node.get("credentials", {})
        if not isinstance(creds, dict):
            continue
        for cred_name, cred_body in creds.items():
            counts.setdefault(cred_name, set()).add(node.get("name", "?"))
            blob = str(cred_body)
            name_l = cred_name.lower()
            if any(h in name_l for h in _OVERSCOPED_HINTS):
                findings.append(_finding(
                    "FS008", node,
                    f"Credential '{cred_name}' is named like an all-powerful account "
                    "(admin/root/owner). Blast radius on compromise is the whole upstream system.",
                    "Create least-privilege credentials per integration and per workflow.",
                    severity="medium",
                ))
            if isinstance(cred_body, dict):
                ctype = str(cred_body.get("_type", ""))
                if ctype and not any(ctype.startswith(p) for p in known_prefixes):
                    findings.append(_finding(
                        "FS008", node,
                        f"Unusual credential type '{ctype}' on node '{node.get('name')}' - "
                        "community/unknown credential handling deserves manual review.",
                        "Verify the credential source and scope before trusting the workflow.",
                        severity="low",
                    ))
    return findings


def rule_expression_command_injection(wf):
    """FS009 - Expressions interpolating $json/$node into shell-ish parameters."""
    findings = []
    targets = ("n8n-nodes-base.executeCommand", "n8n-nodes-base.ssh")
    for node in _iter_nodes(wf):
        if node.get("type") not in targets:
            continue
        cmd = _node_param(node, "command")
        if _EXPRESSION_RE.search(cmd) and ("$json" in cmd or "$node" in cmd or "$(" in cmd):
            findings.append(_finding(
                "FS009", node,
                "Command is built from workflow data ($json/$node expressions). Upstream "
                "attacker-controlled content becomes shell metacharacters.",
                "Never interpolate data into commands; use argv-style APIs or strict "
                "allowlist validation of the entire command string.",
                severity="critical",
                evidence=cmd[:80],
            ))
    return findings


def rule_error_handling(wf):
    """FS010 - Workflow without any error handling settings."""
    findings = []
    settings = wf.get("settings", {})
    has_error_workflow = bool(settings.get("errorWorkflow"))
    has_error_trigger = any(
        n.get("type") == "n8n-nodes-base.errorTrigger" for n in _iter_nodes(wf)
    )
    if not has_error_workflow and not has_error_trigger:
        wf_name = wf.get("name", "?")
        findings.append({
            "rule_id": "FS010",
            "severity": "medium",
            "title": RULES_META["FS010"][0],
            "node_name": wf_name,
            "node_type": "workflow",
            "message": "Workflow has no errorWorkflow setting and no Error Trigger node. "
                       "Failures (and the data inside them) go nowhere visible.",
            "remediation": "Attach an error workflow in Settings > Error Workflow, or add an "
                           "Error Trigger workflow that alerts a human.",
        })
    return findings


def rule_sql_injection(wf):
    """FS011 - SQL text built from expressions."""
    findings = []
    for node in _iter_nodes(wf):
        ntype = node.get("type", "")
        if "sql" not in ntype.lower() and "postgres" not in ntype.lower() and "mysql" not in ntype.lower():
            continue
        query = _node_param(node, "query") or _node_param(node, "operation")
        if query and _SQL_PATTERN.search(query) and _EXPRESSION_RE.search(query):
            findings.append(_finding(
                "FS011", node,
                "SQL statement is concatenated from workflow expressions - textbook "
                "second-order SQL injection if any upstream value is user-controlled.",
                "Use parameterized queries ($queryReplacement / bind parameters) instead of "
                "string interpolation.",
                severity="high",
                evidence=query[:80],
            ))
    return findings


def rule_plain_http(wf):
    """FS012 - HTTP nodes calling plain http:// URLs."""
    findings = []
    for node in _iter_nodes(wf):
        if node.get("type") != "n8n-nodes-base.httpRequest":
            continue
        url = _node_param(node, "url").strip()
        if url.lower().startswith("http://") and not _EXPRESSION_RE.search(url):
            findings.append(_finding(
                "FS012", node,
                f"HTTP node sends requests over plain http:// ({url.split('?')[0]}). "
                "Credentials and payloads are visible to anyone on the path.",
                "Use https:// endpoints; if the target cannot do TLS, put it behind a tunnel "
                "or private network.",
                severity="high",
                evidence=url[:60],
            ))
    return findings


def rule_exposed_trigger(wf):
    """FS013 - Form/Telegram/emailTrigger nodes that accept unauthenticated input."""
    findings = []
    exposed = {
        "n8n-nodes-base.formTrigger": "Form Trigger accepts public submissions",
        "n8n-nodes-base.telegramTrigger": "Telegram Trigger processes unverified messages",
        "n8n-nodes-base.emailReadImap": "IMAP trigger processes attacker-emailable input",
    }
    for node in _iter_nodes(wf):
        ntype = node.get("type", "")
        if ntype in exposed:
            findings.append(_finding(
                "FS013", node,
                f"{exposed[ntype]}. Downstream nodes must treat all input as hostile "
                "(never interpolate into commands/SQL/code).",
                "Add validation + allowlists at the top of the workflow; keep FS005/FS007/FS011 "
                "clean for these paths.",
                severity="medium",
            ))
    return findings


def rule_credential_reuse(wf):
    """FS014 - Same credential wired into many nodes (lateral movement highways)."""
    findings = []
    usage = {}
    for node in _iter_nodes(wf):
        creds = node.get("credentials", {})
        if not isinstance(creds, dict):
            continue
        for cred_name in creds:
            usage.setdefault(cred_name, 0)
            usage[cred_name] += 1
    for cred_name, count in usage.items():
        if count >= 5:
            findings.append({
                "rule_id": "FS014",
                "severity": "medium",
                "title": RULES_META["FS014"][0],
                "node_name": cred_name,
                "node_type": "credential",
                "message": f"Credential '{cred_name}' is used by {count} nodes in one workflow. "
                           "A single prompt-injection or SSRF pivot exposes all of them.",
                "remediation": "Split workflows by trust boundary and scope credentials per workflow.",
            })
    return findings


def rule_community_nodes(wf):
    """FS015 - Non-official node packages (community nodes are arbitrary npm code)."""
    findings = []
    for node in _iter_nodes(wf):
        ntype = node.get("type", "")
        if not ntype.startswith("n8n-nodes-") and not ntype.startswith("@"):
            findings.append(_finding(
                "FS015", node,
                f"Node type '{ntype}' is not an official n8n package - community nodes run "
                "third-party npm code inside your instance with full API access.",
                "Pin the community package version, review its source, and disable install "
                "rights in production (N8N_COMMUNITY_PACKAGES_ENABLED).",
                severity="medium",
            ))
    return findings


def rule_data_exfil(wf):
    """FS016 - Webhooks/HTTP sending workflow data to generic external sinks."""
    findings = []
    sinks = ("webhook.site", "requestbin", "pipedream", "ngrok", "pastebin", "discord.com/api/webhooks")
    for node in _iter_nodes(wf):
        if node.get("type") != "n8n-nodes-base.httpRequest":
            continue
        url = _node_param(node, "url")
        for sink in sinks:
            if sink in url.lower():
                findings.append(_finding(
                    "FS016", node,
                    f"HTTP node posts to '{sink}' - commonly used for debugging or as an "
                    "exfiltration sink. Workflow data (emails, tokens, PII) leaves your control.",
                    "Remove debug sinks before production; route integrations through "
                    "allowlisted domains.",
                    severity="medium",
                    evidence=url[:60],
                ))
                break
    return findings


def rule_webhook_response(wf):
    """FS017 - Webhook respond modes that echo internal data back."""
    findings = []
    for node in _iter_nodes(wf):
        if node.get("type") != "n8n-nodes-base.webhook":
            continue
        params = node.get("parameters", {})
        response_mode = params.get("responseMode", "onReceived")
        if response_mode in ("responseNode", "lastNode"):
            findings.append(_finding(
                "FS017", node,
                f"Webhook responseMode='{response_mode}' - the last node's full output "
                "(possibly including credentials, internal IDs, stack traces) is returned "
                "to the unauthenticated caller.",
                "Return an explicit minimal payload via the Respond to Webhook node.",
                severity="medium",
            ))
    return findings


def rule_set_secrets(wf):
    """FS018 - Set/Edit Fields nodes writing secret-looking literal values."""
    findings = []
    for node in _iter_nodes(wf):
        ntype = node.get("type", "")
        if ntype not in ("n8n-nodes-base.set", "n8n-nodes-base.editImage"):
            if "set" not in ntype.lower():
                continue
        params = node.get("parameters", {})
        assignments = params.get("assignments", {})
        for item in assignments.get("assignments", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            value = str(item.get("value", ""))
            if (_SECRET_KEY_RE.search(name) and value
                    and "{{" not in value and len(value) >= 6):
                findings.append(_finding(
                    "FS018", node,
                    f"Set node stores literal secret-like value in field '{name}' - plaintext "
                    "in the workflow export and execution data.",
                    "Reference credentials via expressions; never paste secrets into Set nodes.",
                    severity="medium",
                    evidence=f"{name}={value[:4]}***",
                ))
    return findings


ALL_RULES = [
    rule_webhook_no_auth,
    rule_hardcoded_secret_params,
    rule_hardcoded_secret_http,
    rule_ssrf_metadata,
    rule_execute_command,
    rule_code_node,
    rule_dynamic_code,
    rule_credential_overscoping,
    rule_expression_command_injection,
    rule_error_handling,
    rule_sql_injection,
    rule_plain_http,
    rule_exposed_trigger,
    rule_credential_reuse,
    rule_community_nodes,
    rule_data_exfil,
    rule_webhook_response,
    rule_set_secrets,
]
