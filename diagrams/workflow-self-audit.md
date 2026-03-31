---
title: "Workflow: Audit and Integrate"
role: diagram
last_updated: 2026-03-31
depends_on: []
freshness: current
scope: platform
---

# Workflow: Audit and Integrate

Visual rendering of the two-phase workflow powered by the MCP skill.

## Phase 1: /audit

```mermaid
flowchart TD
    start([Clone target repo]) --> open[Open repo in Cursor]
    open --> audit[Run /audit]
    audit --> branch[Agent verifies prod branch]
    branch --> explore[Agent explores repo structure]
    explore --> generate[Agent produces structured report]
    generate --> save[audit.md saved in repo root]
    save --> review{Human review}
    review --> correct[Correct errors]
    correct --> fill[Fill unknowns]
    fill --> flag[Flag contradictions]
    flag --> ready([Ready to integrate])
```

## Phase 2: /integrate {repo-name}

```mermaid
flowchart TD
    start([Run /integrate in MCP]) --> copy[Copy audit to audits/repo-name.md]
    copy --> inv[Update INVENTORY.md]
    inv --> prio[Update PRIORITY_CLONES.md]
    prio --> maps{Cross-cutting findings?}

    maps -->|Yes| dep[Update dependency matrix]
    dep --> deploy[Update deployment flow]
    deploy --> sot[Update source of truth]
    sot --> contra[Update contradictions]
    contra --> stale[Update stale assumptions]
    stale --> docs[Update missing docs]
    docs --> simp[Update candidate simplifications]
    simp --> diagrams[Flag diagram updates]
    diagrams --> done([Done])

    maps -->|No| done
```

## The Compounding Loop

```mermaid
flowchart LR
    audit["/audit"] --> review[Human Review]
    review --> integrate["/integrate"]
    integrate --> maps[Maps Updated]
    maps --> understanding[Platform Understanding Improves]
    understanding -->|Next audit is better| audit
```

Each audit feeds the shared model. The shared model makes the next audit more effective. This is the core value loop of Master Control Protocol.
