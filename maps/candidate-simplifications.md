---
depends_on:
- INVENTORY.md
- audits/*
freshness: current
last_updated: '2026-03-31'
role: map
scope: platform
title: Candidate Simplifications
---

# Candidate Simplifications

Concrete opportunities to reduce complexity across the platform. The point is not just to describe the current system, but to identify practical ways to improve it.

This file turns platform understanding into platform improvement.

---

## Simplification Types

- Consolidating repos
- Eliminating dead code
- Removing duplicate responsibilities
- Reducing overlapping configuration
- Simplifying deployment paths
- Streamlining operational workflows
- Clarifying ownership boundaries
- Reducing surface-area sprawl

---

## Effort Tiers

| Tier | Effort | Duration | Risk |
|---|---|---|---|
| **Tier 1** | Quick wins, low effort | < 1 sprint | Low risk |
| **Tier 2** | Medium effort | 1–3 sprints | Moderate risk |
| **Tier 3** | Significant effort | 3+ sprints | Higher risk |

---

## Catalog

| ID | Description | Type | Repos Involved | Tier | Impact | Status | Source |
|---|---|---|---|---|---|---|---|
| SIM-001 | Config 'pyproject.toml' referenced in 3 repos | config-sprawl | python-build-standalone, ruff, ruff-pre-commit | 1 | medium | proposed | synthesize/simplifications |
| SIM-002 | 4 repos share CI/CD pattern: github actions/github actions | pipeline-redundancy | python-build-standalone, ruff-pre-commit, ruff-vscode, setup-uv | 2 | medium | proposed | synthesize/simplifications |
| SIM-003 | ruff-pre-commit is a thin wrapper around ruff | consolidation-candidate | ruff, ruff-pre-commit | 2 | low | proposed | synthesize/simplifications |
| SIM-004 | ruff and uv have overlapping purposes | duplicate-functionality | ruff, uv | 3 | medium | proposed | synthesize/simplifications |
| SIM-005 | Python repos use different build tools | library-fragmentation | python-build-standalone, ruff, ruff-pre-commit, ruff-vscode, uv | 3 | low | proposed | synthesize/simplifications |
| SIM-006 | Rust repos use different build tools | library-fragmentation | python-build-standalone, ruff, uv | 3 | low | proposed | synthesize/simplifications |
| SIM-007 | Typescript repos use different build tools | library-fragmentation | ruff, ruff-vscode, setup-uv | 3 | low | proposed | synthesize/simplifications |

**Type values:** `duplication` · `dead code` · `unnecessary coupling` · `over-abstraction` · `consolidation` · `deprecation candidate` · `deployment simplification` · `config reduction` · `ownership clarification` · `other`

---

## Impact Matrix

Compare opportunities across multiple dimensions to inform prioritization.

| ID | Effort | Risk | Repos Reduced | Complexity Reduction | Operational Benefit | Notes |
|---|---|---|---|---|---|---|
| X-001 | low · medium · high | low · medium · high | | low · medium · high | low · medium · high | |

---

## Recommended Execution Order

Based on the impact matrix, suggested sequencing for simplification work. Start with high-impact, low-effort items to build momentum.

| Priority | ID | Description | Rationale |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## Recurring Themes

Simplification patterns that appear across multiple repos, suggesting systemic opportunities rather than one-off cleanups.

| Theme | Occurrences | Notes |
|---|---|---|
| Duplicated configuration across repos | | |
| Repos that could be merged | | |
| Shared libraries that should be extracted | | |
| Dead or unused code paths | | |
| Over-engineered abstractions | | |
| Services that could be replaced with managed alternatives | | |
