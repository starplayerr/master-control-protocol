# Master Control Protocol

A documentation-first platform audit hub for mapping, auditing, and reasoning about multi-repo technical ecosystems.

## The Problem

In large platforms spanning dozens of repositories — EKS clusters, SageMaker pipelines, Jupyter extensions, SDKs, GPU management, image builds, infra stacks — the real bottleneck is rarely implementation skill. It is **orientation**.

Engineers lose time figuring out:

- Where to start when making a change
- Which repo actually owns a behavior
- Which repo deploys what
- Where configuration truly lives
- What depends on what
- What is stale, ambiguous, or contradictory

Traditional documentation is scattered, repo-local, outdated, too shallow, and dependent on tribal knowledge.

## What This Is

Master Control Protocol is a **central audit and architecture hub** for complex multi-repo platforms. It uses structured Markdown reports, standardized self-audit prompts, inventory tracking, and cross-cutting maps to make dependencies, deployment flow, ownership, and sources of truth visible.

Instead of relying on tribal knowledge or scattered docs, it creates a **living operational map** of the system.

It sits in the middle layer between tribal knowledge and overengineered automation fantasies — lightweight enough to actually maintain, structured enough to create real leverage.

## Repo Structure

```
master-control-protocol/
├── README.md                         ← You are here
│
│── Tracking
├── INVENTORY.md                      ← Full catalog + canonical counts
├── PRIORITY_CLONES.md                ← Audit queue, sequencing, outcomes
│
│── Workflow
├── .cursor/skills/mcp-workflow/
│   ├── SKILL.md                      ← /audit and /integrate skill
│   ├── audit-prompt.md               ← Structured audit prompt
│   └── post-audit-checklist.md       ← Integration steps
│
│── Automation
├── scripts/                          ← Automated audit pipeline
│   ├── discover.py                   ← GitHub org repo discovery
│   ├── audit.py                      ← Single-repo audit runner
│   ├── run_all.py                    ← Full pipeline orchestrator
│   └── lib/                          ← Shared library modules
├── prompts/                          ← Repo-type-specific audit prompts
│   ├── default.md
│   ├── infrastructure.md
│   ├── library.md
│   ├── service.md
│   └── frontend.md
├── audit-state.json                  ← Cache: tracks audit staleness
│
│── Knowledge
├── audits/                           ← Stored repo audit reports
│   └── <repo-name>.md
├── maps/                             ← Platform synthesis layer
│   ├── dependency-matrix.md
│   ├── deployment-flow.md
│   ├── source-of-truth.md
│   ├── contradictions-and-ambiguities.md
│   ├── stale-assumptions.md
│   ├── missing-docs.md
│   └── candidate-simplifications.md
├── diagrams/                         ← Human-readable visuals
│   ├── dependency-matrix.md
│   ├── deployment-flow.md
│   ├── eks-infra-stack.md
│   └── workflow-self-audit.md
└── reports/                          ← Periodic dated synthesis reports
    └── report-template.md
```

## How It Works

### The Workflow

Master Control Protocol uses a Cursor skill with two commands:

**`/audit`** — Run in a cloned target repo. The agent reads the audit prompt, verifies the prod branch, explores the repository, and produces a structured Markdown report saved as `audit.md` in the repo root.

**`/integrate {repo-name}`** — Run in MCP after reviewing the audit. The agent copies the audit into `audits/`, updates `INVENTORY.md` and `PRIORITY_CLONES.md`, reviews each map for cross-cutting findings, and flags diagrams that may need updating.

### The Compounding Loop

1. **Audit a repo** — Run `/audit` in the target repo
2. **Review critically** — Correct errors, fill unknowns, flag contradictions
3. **Integrate findings** — Run `/integrate {repo-name}` in MCP
4. **Platform understanding improves** — Each audit makes the next one better

### Tracking

[INVENTORY.md](INVENTORY.md) is the full catalog of known repositories with canonical top-line counts (total repos, audited, coverage).

[PRIORITY_CLONES.md](PRIORITY_CLONES.md) is the audit queue — which repos to audit next, why, and what was learned after each one.

### Knowledge

- **`audits/`** — Stored copies of repo audits for historical traceability
- **`maps/`** — Cross-cutting findings: dependencies, contradictions, staleness, gaps, simplifications
- **`diagrams/`** — Human-readable Mermaid visuals
- **`reports/`** — Periodic dated synthesis reports from accumulated findings

### Automated Pipeline

For bulk auditing, MCP includes a Python-based pipeline that replaces the manual loop entirely:

```bash
pip install -r requirements.txt
# Set GITHUB_TOKEN and ANTHROPIC_API_KEY in .env
python scripts/run_all.py --org <your-github-org>
```

This discovers all repos in the org, checks which need auditing, runs audits in parallel via the LLM, and updates `INVENTORY.md` automatically. Prompts are auto-selected based on repo type (infrastructure, service, library, frontend) or overridden manually. See [scripts/README.md](scripts/README.md) for full usage.

## What It Is Good For

| Use Case | How It Helps |
|---|---|
| **Change planning** | Identify likely repo touchpoints and source-of-truth locations before touching anything |
| **Security review** | Surface unclear ownership, mystery dependencies, stale assumptions, undocumented secrets, hidden config paths |
| **Onboarding** | New engineers get a structured map instead of reverse-engineering from scattered READMEs |
| **Platform simplification** | Contradictions and duplication become visible, enabling intentional complexity reduction |
| **AI-assisted engineering** | Agents work better with repeatable audit structure than vague prompts |

## Generalizing Beyond One Platform

The original context was a platform spanning EKS, SageMaker, Jupyter, extensions, SDKs, and GPU management. But the structure is deliberately generalizable.

To adapt for another ecosystem:

1. Populate [INVENTORY.md](INVENTORY.md) with your repos
2. Run `/audit` against priority repos
3. Integrate findings with `/integrate`
4. Build out [maps](maps/) as patterns emerge
5. Render [diagrams](diagrams/) for visual orientation
6. Produce periodic [reports](reports/) to synthesize accumulated understanding

The format works for any multi-repo platform where orientation is the bottleneck.
