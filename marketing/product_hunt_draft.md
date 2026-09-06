# Product Hunt Launch Draft — FlowSentry v0.1.0 (READY, NOT PUBLISHED)

Status: draft complet, cont PH nepublicat (Cloudflare challenge blochează signup-ul din browserul stației — reîncearcă de pe alt IP/browser).
Când publicăm: marți–joi, 00:01–07:00 PT (12:01–17:00 EEST) pentru trafic maxim US+EU.

---

## Tagline (60 chars max)
"Security scanner for n8n workflows — catch leaks before prod"

Alternative:
- "Find exposed webhooks & leaked secrets in your n8n exports"
- "18-rule static analysis for n8n workflow JSON"

## One-liner (first comment pinned)
n8n webhooks are unauthenticated by default, and every exported workflow JSON can leak
credentials or shell-injection paths. FlowSentry is a free, Apache-2.0 CLI that scans
your workflow exports statically — 18 rules mapped to OWASP Agentic Top 10 — and fails
your CI when it finds critical issues. Zero dependencies, pure Python 3.9+.

## Description
FlowSentry parses n8n workflow JSON exports and flags:

• Webhooks with authentication: none (the default!)
• Hardcoded API keys, tokens and passwords in node parameters and headers
• Execute Command nodes interpolating {{$json...}} into shell commands
• Eval-style Code nodes and expression-based injection
• SSRF to cloud metadata endpoints (169.254.169.254 etc.)
• SQL built from expressions, over-scoped credentials, exfil sinks

Output: terminal, JSON, SARIF 2.1.0 (GitHub Code Scanning), HTML.
`pip install flowsentry` → `flowsentry scan ./workflows`
Exit code 1 on critical/high → drop it into CI as a gate.

We scanned 10 random public n8n workflows on GitHub: 11 critical + 39 medium findings,
100% of files had at least one. Full methodology + sources in the README.

No account. No telemetry. Reads local files, sends no requests. Self-host everything.

## Topics
developer-tools, security, open-source, github, cli, devsecops

## Gallery plan
1. Terminal screenshot: scan run on a real workflow showing critical findings (use docs/demo.gif frame style)
2. HTML report screenshot
3. SARIF → GitHub Code Scanning integration screenshot

## First comment (maker comment, pinned)
Why we built it: while reviewing public n8n workflow exports we kept seeing
`authentication: none` webhooks and API keys in plain text. Static analysis for n8n
JSON didn't exist, so we built it — as an autonomous-AI-agent-run project with human
review (the scanner itself has zero AI, it's deterministic static analysis).

Free forever (Apache-2.0): https://github.com/vasilicasijarvis/flowsentry
Docs + live demo: https://flowsentry.vercel.app
PyPI: https://pypi.org/project/flowsentry/

Ask: run it against your own exported workflows and tell us what it caught (or the
false positives you'd want tuned).

## Launch-day checklist
- [ ] Mihai: post from his own PH account (voting credibility; PH favors makers with history)
- [ ] Prepare 2–3 reply templates for common comments (Windows support? GitLab CI? n8n cloud?)
- [ ] Sync launch with forum.n8n.io post approval + Show HN (H+1 day)
- [ ] Watch PyPI download stats + GitHub stars same evening
