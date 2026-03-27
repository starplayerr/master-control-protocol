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
├── README.md                 ← You are here
├── inventory.md              ← Central catalog of repos and audit state
├── surfaces.md               ← Platform surfaces (functional domains)
├── initial-report.md         ← First-pass synthesis after inventorying
├── audit-template.md         ← Standardized self-audit process + Copilot prompt
├── audits/                   ← Per-repo audit reports
│   └── <repo-name>.md
├── maps/                     ← Platform synthesis layer across repos
│   ├── dependency-matrix.md
│   ├── deployment-flow.md
│   ├── source-of-truth.md
│   ├── contradictions-and-ambiguities.md
│   ├── stale-assumptions.md
│   ├── missing-docs.md
│   └── candidate-simplifications.md
└── diagrams/                 ← Mermaid diagrams for visual understanding
    ├── dependency-matrix.md
    ├── deployment-flow.md
    ├── eks-infra-stack.md
    └── workflow-self-audit.md
```

## How It Works

### The Compounding Loop

1. **Audit a repo** — Use the [audit template](audit-template.md) with Copilot Agent mode
2. **Save findings** — Store the report in `audits/<repo-name>.md`
3. **Update inventory** — Mark the repo as audited in [inventory.md](inventory.md)
4. **Update shared maps** — Feed findings into the [maps](maps/)
5. **Improve platform understanding** — Each audit makes the next one better

### Running a Self-Audit

1. Open the target repo in VS Code with GitHub Copilot Agent mode.
2. Check the active branch — verify it represents prod-deployed code (usually `main` or `master`, but not always).
3. Check deployment indicators (Spinnaker config, `triggerable.yaml`, etc.).
4. Copy the prompt from [audit-template.md](audit-template.md) into Copilot Chat.
5. Let Copilot explore the repo and produce the report.
6. Save the output as `audits/<repo-name>.md` in this repo.
7. Review critically — correct errors, fill unknowns, flag contradictions.
8. Update [inventory.md](inventory.md).
9. Update [maps](maps/) if new dependencies or relationships were found.

### Updating Maps

When a new audit reveals findings:

1. Review each map
2. Update dependencies
3. Update deployment paths
4. Update source-of-truth assumptions
5. Update contradictions or ambiguities
6. Add new missing docs or simplification candidates

Repo audits are not isolated artifacts. They feed into the larger shared model of the platform.

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

1. Define your [surfaces](surfaces.md) (functional domains)
2. Populate [inventory.md](inventory.md) with your repos
3. Run self-audits using the [template](audit-template.md)
4. Build out [maps](maps/) as patterns emerge
5. Render [diagrams](diagrams/) for visual orientation

The format works for any multi-repo platform where orientation is the bottleneck.
