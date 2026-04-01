---
title: "Priority Clones"
role: queue
last_updated: 2026-03-31
depends_on:
  - INVENTORY.md
freshness: draft
scope: platform
---

# Priority Clones

Audit queue, sequencing, and high-level outcomes. This file tracks which repos should be cloned and audited next, in what order, and what was learned.

In a real deployment backed by a database, this queue can be constructed dynamically from accumulated findings — repos surfaced by dependency analysis, contradiction discovery, or gap identification get promoted automatically. In Markdown form, it is maintained manually as audits accumulate.

## Audit Queue

| # | Repo | Surface | Why Prioritized | Expected Outcome | Status |
|---|---|---|---|---|---|
| | | | | | |

**Status values:** `queued` · `in progress` · `audited` · `deferred`

## How to Use

- Add repos when audits, maps, or team conversations reveal they should be examined next.
- Sequence by expected leverage: repos with high dependency surface, unclear ownership, or known contradictions should go first.
- After completing an audit via `/integrate`, update the status to `audited` and add an outcome summary below.
- Re-evaluate sequencing as new findings shift priorities.

## Outcomes

Short summaries of what each completed audit revealed. These help inform future prioritization.

| Repo | Date Audited | Outcome |
|---|---|---|
| | | |
