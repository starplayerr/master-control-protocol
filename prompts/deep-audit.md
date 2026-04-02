---
title: "Deep audit (human + high-context LLM)"
role: template
last_updated: 2026-04-01
depends_on: []
freshness: current
scope: per-repo
---

# Deep audit template

Use this template when a **human** runs a **thorough** repo audit with a high-context model (e.g. Copilot Agent, Claude Opus) and a **local clone**. It is **not** the same as the automated pipeline prompts (`default.md`, `library.md`, …): those are tuned for scripted `audit.py` runs with a bounded file context. This document is the **gold-standard** depth: read real source, integrate KT and tribal knowledge, optional ASCII diagrams, cross-repo comparisons, and nuanced contradictions with impact.

The synthesis layer ([scripts/synthesize/extract.py](../scripts/synthesize/extract.py)) normalizes and cross-references what you produce here—it does not replace reading the code.

**Safety:** The audit pipeline honors [.mcpignore](../.mcpignore) in this MCP repo and optional `.mcpignore` in the target repo—those paths are never sent to an LLM. Do not paste secrets into the chat; keep them out of the report or redact.

---

## Pre-audit checklist

- [ ] Open the target repo in your editor with the model in agent mode (or equivalent).
- [ ] Confirm the branch that reflects production (or the scope you are auditing)—not always `main`.
- [ ] Pull latest; note commit SHA and prod branch if different.
- [ ] Gather KT notes, runbooks, or tribal knowledge you will weave into the report (SNS/SQS flows, auth patterns, AZ behavior, etc.).
- [ ] Add `audit.md` to the target repo’s `.gitignore` if you save a scratch copy there—or save only under MCP `audits/<repo-name>.md`.

---

## Depth expectations (beyond shallow metadata)

- **Read actual source**, not only top-level manifests: e.g. `providers.tf`, `vars.go`, Dockerfiles, entrypoints, auth middleware, feature flags.
- **Runtime behavior:** Where things execute (image vs host, init vs shell), upgrade paths, sidecars—when it matters for dependencies or risk.
- **Dependency semantics:** Edges are not just names—note type (library, RPC, queue, shared config) and **why** the relationship exists when you can infer it from code.
- **Cross-repo:** If this repo interacts with another (e.g. ingress vs API), call out **divergences** (auth, contracts, versions) and **impact**.
- **Contradictions:** Tabulate conflicts with docs, other audits, or reality; include **severity** and **suggested resolution** where possible.
- **Optional:** ASCII diagrams for flows or dependency sketches when they clarify what prose cannot.

---

## The prompt (copy below into your agent)

Copy everything inside the outer code block into chat. Replace placeholders as needed.

```
You are performing a structured, high-depth self-audit of this repository. Your goal is a comprehensive Markdown report: identity, purpose, tech stack, deployment, dependencies (semantic, not just names), configuration sources of truth, API surface, secrets handling, known gaps, owner/bus-factor, and—where relevant—cross-repo comparisons and contradictions with impact analysis.

Go beyond manifests: open and reason about source files that define behavior (e.g. Terraform, Go/Rust/Python/TS entrypoints, Dockerfiles, CI workflows). Integrate any KT or organizational context the human provides in this session.

Inspect the following where they exist (extend as needed for this stack):

- Directory tree (understand layout; deep-read critical paths)
- README
- go.mod / go.sum, package.json, pyproject.toml / requirements.txt, Cargo.toml, etc.
- Dockerfile / docker-compose, Helm/Kustomize/Terraform as present
- Main source entry points, auth, and integration boundaries
- CI/CD definitions

Produce the report in the exact section structure below. Use "unknown" when you cannot determine something—do not invent. For contradictions and cross-repo issues, be explicit about evidence (file paths, snippets) and impact.

Respond ONLY with the Markdown report.

---

# Audit: <repo-name>

**Date:** YYYY-MM-DD
**Auditor:** <model> (reviewed by: <human>)
**Branch audited:** <branch>
**Prod branch (if different):** <branch or "same">

## Identity

| Field | Value |
|---|---|
| Repo name | |
| GitHub URL | |
| Owner(s) | |
| Last meaningful commit | |
| Prod status | active · deprecated · disabled · unknown |
| Purpose | |

## Tech Stack

| Field | Value |
|---|---|
| Language(s) | |
| Framework(s) | |
| Build tool(s) | |
| Runtime | |

## Artifacts Produced

| Artifact | Type | Registry | Destination |
|---|---|---|---|
| | | | |

## Deployment

| Field | Value |
|---|---|
| CI system | |
| CD system | |
| Target environment(s) | |
| Pipeline file(s) | |

## Dependencies

### Outbound (what this repo depends on)

| Dependency | Type | Notes |
|---|---|---|
| | | |

### Inbound (what depends on this repo)

| Consumer | Type | Notes |
|---|---|---|
| | | |

### Dependency diagram (optional)

ASCII or structured summary of critical edges and runtime flows if helpful.

## Config / Sources of Truth

Where does this repo get its configuration? List every external config source.

| Config | Source | Notes |
|---|---|---|
| | | |

## API Surface

| Endpoint / Interface | Port | Protocol | Auth | Notes |
|---|---|---|---|---|
| | | | | |

## Secrets and Auth

| Secret / Credential | Source | Used For |
|---|---|---|
| | | |

(Do not paste secret values—describe location and usage only.)

## Cross-repo and contradictions

| ID | Topic | Evidence | Impact | Suggested resolution |
|---|---|---|---|---|
| | | | | |

## Known Gaps

List anything concerning, unclear, or missing:

-
-
-

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors?
- Bus factor concerns?
- Confidence level: high · medium · low · unknown

---

Save the final report as `audits/<repo-name>.md` in the Master Control Protocol workspace (or `audit.md` locally for review first—do not commit secrets).
```

---

## Post-audit steps

1. **Review critically** — correct errors; redact any accidental secrets.
2. **Fill unknowns** with human or teammate input where possible.
3. **Copy into MCP** as `audits/<repo-name>.md` and integrate per [.cursor/skills/mcp-workflow/SKILL.md](../.cursor/skills/mcp-workflow/SKILL.md) or your team process.
4. **Update** `INVENTORY.md`, maps, and contradiction registers as findings warrant.

## Why this coexists with automated prompts

Automated prompts feed the scripted audit path and bounded context. This template targets **maximum signal** when a senior engineer plus a strong model can read the codebase directly. The synthesis engine scales and cross-references the output—it is the librarian, not the auditor.
