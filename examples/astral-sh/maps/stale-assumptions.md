---
depends_on:
- INVENTORY.md
- audits/*
freshness: current
last_updated: '2026-03-31'
role: map
scope: platform
title: Stale Assumptions
---

# Stale Assumptions

Items across the repo ecosystem that appear outdated, abandoned, deprecated, or based on assumptions that may no longer hold. Sorted by risk level so cleanup and verification can be prioritized.

This file helps separate live architecture from historical residue.

---

## High Risk: Deployed but Unwanted

Repos or components that may still be running in production even though they are flagged as deprecated, replaced, or scheduled for removal.

| Item | Status | Risk | Action | Source |
|---|---|---|---|---|
| | deprecated · replaced · scheduled for removal | | | |

---

## Medium Risk: Should Be Deleted

Repos that team inventory says can be deleted, but which still exist in the org and continue to create confusion. These are especially dangerous for onboarding because people may mistake dead repos for active ones.

| Repo | Team Note | Risk | Recommended Action | Source |
|---|---|---|---|---|
| | | | | |

---

## Moderate Risk: Stale but Dormant

Repos, services, or assumptions that may not be actively harmful, but still appear to reflect outdated realities.

| Assumption | Reality Check | Question | Action | Source |
|---|---|---|---|---|
| ruff claims 'ruff-action' depends on it | No audit exists for 'ruff-action' — cannot verify this consumer | Verify | needs-verification | audits/ruff.md |
| setup-uv config references 'astral-sh/versions' | No audit exists for 'versions' | Verify | needs-verification | audits/setup-uv.md |
| ruff-vscode uses or references a deprecated pattern | ruff-lsp is deprecated in favour of Ruff's native language server | Verify | high | audits/ruff-vscode.md |

---

## Low Risk: Housekeeping

Non-prod demos, POCs, sample code, or abandoned experiments that add clutter but are not urgent.

| Repo | Type | Action | Source |
|---|---|---|---|
| | demo · POC · sample · experiment · other | archive · delete · document · ignore | |

---

## Verification Checklist

Track the status of stale-assumption verification work.

| # | Check | Tool / Method | Status |
|---|---|---|---|
| 1 | | | not started · in progress · verified · still stale |
| 2 | | | not started · in progress · verified · still stale |
| 3 | | | not started · in progress · verified · still stale |

---

**Last updated:** —
**Stale items identified:** —
**Source repos / validation method:** —
