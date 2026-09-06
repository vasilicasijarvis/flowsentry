# FlowSentry — Reddit Launch Drafts (researched, rule-compliant)

Researched 06.09.2026. Sources: r/n8n rules (mod post + 3 independent rule trackers,
Aug 2026), r/selfhosted rules (Rule 7/8 sidebar text via community mirrors, Jun 2026),
r/selfhosted New Project Megathread policy (week of 27 Aug 2026).

## TL;DR — DO NOT post a launch post in r/n8n. Megathread-only in r/selfhosted.

---

## 1. r/n8n — rules verified (Aug 2026)

1. No Spam & No Clickbait
2. No AI Slop
3. **No Self-Promotion or Advertising** — "Do not promote your own tools, SaaS products,
   paid services, courses, or platforms."  ← FlowSentry launch post = removed
4. No Business, Agency, or Client-Related Posts
5. No Links to Paid Workflows, Paid Communities, or Signup-Required Content
6. Recruiting and Hiring
7. All Workflow and Video Posts Must Include the Code
8. No Google Drive or Google Docs Links
9. Use the Correct Post Flair
10. Low Quality or Off Topic
11. Keep it civil

### Play A (recommended first): modmail permission ask
Send the mods a short, honest modmail BEFORE posting anything. Cost: one message.
Risk: zero. Template:

> Subject: Permission to share an open-source n8n security scanner (educational findings)?
>
> Hi mods — I analyzed 10 publicly shared n8n workflow exports from GitHub with a free,
> Apache-2.0 CLI scanner I built. Findings: 5 of 10 had webhooks with authentication
> disabled, one interpolated {{$json.library}} straight into a bash command, one echoed
> full node output back to unauthenticated callers. No instance was accessed — this is
> static JSON analysis, defensive only.
>
> Would you allow (a) an educational post with the findings + full workflow JSON (rule 7
> satisfied) and the repo linked as the tool used, or (b) comment-only participation where
> I answer security questions and link the repo only when directly asked?
>
> Happy to follow whatever fits the sub. — [username]

### Play B (while waiting / regardless): value-first comments
Monitor r/n8n for: "webhook security", "is my n8n exposed", "API key leaked",
"someone triggered my webhook", "n8n hardening". Reply with the technical answer FIRST,
complete, no link. Mention the tool only if asked or when it honestly fits, with
disclosure ("I built an open-source scanner for exactly this — flowsentry on GitHub").
Three prepared comment skeletons:

1. Webhook auth question → explain authentication options (Basic/Header/JWT), the
   reverse-proxy single-point-of-failure trap, and that exports reveal auth settings;
   fix = header auth + shared secret validation node.
2. "Can someone abuse my webhook?" → walk through responseMode data exposure (FS017),
   suggest Respond-to-Webhook with minimal payload + auth + rate limit at proxy.
3. Execute Command / code node worries → N8N_RUNNERS_ENABLED, container isolation,
   never interpolate {{$json...}} into commands (cite the real public example).

### Play C (risky, only with mod approval from Play A): educational PSA post
Title: "I analyzed 10 public n8n workflow exports — 5 of 10 had unauthenticated webhooks"
Body: findings table (same as README), full JSON snippets for rule 7, remediation for
each, repo link ONCE at the end with disclosure: "I built the free OSS scanner I used
(apache-2.0, no signup). Not selling anything here." Do NOT post without mod OK.

---

## 2. r/selfhosted — rules verified (Jun 2026 sidebar text)

Key rules affecting us:
- Rule 7: Promotion posts require 30-day-old account + active participation.
  **F/LOSS Exception**: completely open source + self-hostable in full without payment →
  exempt, provided you keep engaging in comments. FlowSentry qualifies (Apache-2.0, no
  paid tier in the CLI).
- Rule 8: AI-involved promotional posts need tags — **[AIP]** (AI-involved) — plus
  transparent AI disclosure.
- New Project policy (2026): standalone "new project" posts are removed and redirected —
  **new projects (<3 months) go in the weekly New Project Megathread** (posted Fridays,
  comments open all week).

### Play A (the compliant move): Megathread comment, template-followed
Post THIS WEEK's megathread (Friday-posted; comment any day) as a top-level comment:

> **Project Name:** FlowSentry
> **Repo/Website Link:** https://github.com/vasilicasijarvis/flowsentry
>   (landing: https://flowsentry.vercel.app)
> **Description:** Security scanner for n8n workflow exports. Parses your JSON exports
> and flags unauthenticated webhooks, hardcoded secrets, SSRF to cloud metadata
> (169.254.169.254), Execute Command shell injection, eval-style code nodes, SQL built
> from expressions, over-scoped credentials — 18 rules mapped to OWASP Agentic Top 10.
> Zero dependencies, pure Python. Terminal + JSON + SARIF (GitHub Code Scanning) + HTML
> reports. Exit code 1 on critical/high = CI gate.
> **Why:** n8n webhooks are unauthenticated by default and exports leak secrets. I scanned
> 10 random public n8n workflows on GitHub: 11 critical findings, 100% of files had ≥1.
> **Deployment:** `pip install flowsentry` → `flowsentry scan ./workflows`. No server, no
> account, no telemetry — reads local files only. 30 tests, no dependencies to audit.
> **AI Involvement:** Built by an autonomous AI agent (disclosed; agent-run project,
> human-reviewed). The scanner itself contains no AI — it's static analysis.

After posting: reply to every comment within the hour for the first day (F/LOSS exception
requires continued engagement).

### Play B (later, ≥30-day account + karma built): standalone [AIP] post
Title: "[AIP] FlowSentry — open-source security scanner for n8n workflows (Apache-2.0)"
Only if the megathread comment gets traction and mods didn't object. Include the same
AI disclosure. Never duplicate the full README (rule 4) — write original prose.

### What NOT to do
- No standalone launch post in r/n8n (rule 3 — instant removal, burns the account).
- No blog-copy-paste into r/selfhosted (rule 4).
- No untagged AI post (rule 8).
- No second account to dodge the 30-day rule — single honest account.

---

## 3. Non-Reddit channels (no rule friction, do these first)

- **forum.n8n.io (official n8n community)** — has a "Show and Tell" category that WELCOMES
  community tools. Draft:

  > Title: FlowSentry — free open-source security scanner for n8n workflows (18 rules)
  > Body: built because webhook auth defaults + exported secrets keep biting people.
  > Show the 10-workflow findings table, screenshots, install, ask for feedback + edge
  > cases. Link repo. This is the highest-signal launch channel — n8n's own community.

- **GitHub**: the repo itself is the funnel (topics set, README findings, demo GIF).
- **Hacker News**: "Show HN: FlowSentry – Security scanner for n8n workflows" — post
  Tuesday–Thursday 6–9 AM ET for best traffic.

## 4. Execution order
1. forum.n8n.io Show and Tell (highest value, zero risk) — same day.
2. r/selfhosted New Project Megathread comment (this week's thread).
3. r/n8n modmail → wait → comments only until answered.
4. Show HN 1–2 days after forum post (so GH has stars/activity when HN clicks through).
