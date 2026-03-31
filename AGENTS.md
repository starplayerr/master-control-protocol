# MCP Agent Context

## What This Repo Is

Master Control Protocol is a structured memory and reasoning layer
for multi-repo platforms. It is not a codebase — it is a knowledge system.

It contains:
- A catalog of all known repositories (INVENTORY.md)
- Structured audit reports for each repo (audits/)
- Platform-level synthesis maps (maps/)
- Mermaid diagrams (diagrams/)
- LLM prompt templates for automated audits (prompts/)
- Automation scripts for discovery and auditing (scripts/)

## How to Read This Repo

Read files in this order:

1. **This file** — orientation
2. **mcp-manifest.json** — structure, read order, and freshness metadata
3. **INVENTORY.md** — what repos exist and their audit status
4. **PRIORITY_CLONES.md** — audit queue and sequencing
5. **maps/** directory — platform-level synthesis (dependency matrix, deployment flow, source of truth, contradictions, stale assumptions, candidate simplifications, missing docs)
6. **Individual audits** as needed — audits/<repo-name>.md

Every markdown file (except README.md) has YAML frontmatter with `role`, `last_updated`, `depends_on`, and `freshness` fields. Use these to assess what is current and what is stale.

## How to Update This Repo

After any audit or investigation:

1. Save the audit report to `audits/<repo-name>.md`
2. Update `INVENTORY.md` with the new repo's status
3. Update `PRIORITY_CLONES.md` if sequencing has changed
4. Check each file in `maps/` — does the new finding change anything?
5. If yes, update the map and change its frontmatter `freshness` to `current`
6. If a new contradiction or stale assumption was found, add it to the relevant map
7. Run `python scripts/check_freshness.py` to verify no maps are stale

## Frontmatter Schema

All markdown files (except README.md) use this frontmatter:

```yaml
---
title: "Human-readable title"
role: map | catalog | queue | audit | template | diagram | overview
last_updated: 2026-03-31
depends_on:
  - INVENTORY.md
  - audits/*
freshness: current | stale | draft
scope: platform | per-repo
---
```

- **depends_on** enables staleness propagation — if a dependency is newer, this file may be stale
- **freshness** values: `current` (reflects latest audits), `stale` (dependencies changed since last update), `draft` (incomplete)

## What NOT to Do

- Do not treat audit reports as authoritative without verification
- Do not update maps speculatively — only with evidence from audits
- Do not remove entries from contradictions-and-ambiguities.md — resolve them with evidence
- Fields marked "unknown" should stay unknown until verified
- Do not edit mcp-manifest.json unless the repo structure changes (files added/removed)
