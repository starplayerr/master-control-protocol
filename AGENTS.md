# MCP Agent Context

## What This Repo Is

Master Control Protocol is a structured memory and reasoning layer
for multi-repo platforms. It is not a codebase — it is a knowledge system.

It contains:
- A forkable template for auditing any GitHub org
- Automation scripts for discovery, auditing, synthesis, and feedback (scripts/)
- LLM prompt templates: automated pipeline prompts (`prompts/default.md`, etc.) and a **deep manual audit** template (`prompts/deep-audit.md`)
- Empty template files for catalogs, maps, and reports
- A complete example run against astral-sh (examples/astral-sh/)

## .mcpignore and audit safety

Patterns use **gitignore-style** rules (`**`, `*`, `!` negation, etc.), implemented via `pathspec` in `scripts/lib/context.py`.

When `gather_context` runs for a target repository, it merges:

1. **`<MCP_ROOT>/.mcpignore`** — defaults shipped with this repo (secrets, credentials, vendor trees, large build outputs).
2. **`<repo>/.mcpignore`** — optional; maintain in the repo under audit for org-specific exclusions.

Any path that matches is **never read, never included in the directory tree shown to the LLM, and never sent in the audit context**. Extend these files for your environment; do not rely on the LLM to “ignore” secrets.

For a **manual** deep audit in chat, still avoid pasting secret values—describe locations only.

## How to Read This Repo

Read files in this order:

1. **This file** — orientation
2. **mcp-manifest.json** — structure, read order, and freshness metadata
3. **INVENTORY.md** — what repos exist and their audit status (empty template at root)
4. **PRIORITY_CLONES.md** — audit queue and sequencing (empty template at root)
5. **maps/** directory — platform-level synthesis templates
6. **examples/astral-sh/** — complete proof-of-concept run with real data

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

## Repo Layout

The root is a clean, forkable template. Data from a real run lives in `examples/astral-sh/`.

- `scripts/` and `prompts/` are the engine — they stay at root (including `prompts/deep-audit.md` for human-led audits)
- `.mcpignore` at the MCP root defines default exclusions for automated context gathering
- `audits/`, `maps/`, `feedback/`, `diagrams/`, `reports/` are empty templates at root
- `examples/astral-sh/` contains populated data from a proof-of-concept run

## What NOT to Do

- Do not treat audit reports as authoritative without verification
- Do not update maps speculatively — only with evidence from audits
- Do not remove entries from contradictions-and-ambiguities.md — resolve them with evidence
- Fields marked "unknown" should stay unknown until verified
- Do not edit mcp-manifest.json unless the repo structure changes (files added/removed)
