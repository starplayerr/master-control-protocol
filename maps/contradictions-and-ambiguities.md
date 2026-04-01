---
depends_on:
- INVENTORY.md
- audits/*
freshness: current
last_updated: '2026-03-31'
role: map
scope: platform
title: Contradictions and Ambiguities
---

# Contradictions and Ambiguities

Conflicting information across repos, documentation, deployment config, and team understanding.

The purpose is to expose places where the platform may be misunderstood, inconsistently documented, or operating on unresolved assumptions. This file helps prevent false assumptions from hardening into "truth" simply because they were repeated often enough.

---

## Active Contradictions

Places where repos, docs, or configs definitively disagree with each other.

| ID | Source Conflict | Contradiction | Impact | Suggested Resolution | Source |
|---|---|---|---|---|---|
| C-001 | ruff, ruff-pre-commit, ruff-vscode | Package 'ruff' has different versions across repos: 0.15.7 (ruff-vscode), 0.15.8 (ruff-pre-commit, ruff), 2026.38.0 (ruff-vscode) | medium | Verify and resolve | audits/ruff-pre-commit.md, audits/ruff-vscode.md, audits/ruff.md |
| C-002 | ruff, ruff-vscode | ruff-vscode pins ruff==0.15.7 but ruff is at version 0.15.8 | medium | Verify and resolve | audits/ruff-vscode.md, audits/ruff.md |
| C-003 | ruff, ruff-pre-commit, ruff-vscode, setup-uv, uv | Repos in github.com/astral-sh use different owner formats: 'astral-sh' (ruff-pre-commit), 'astral-sh' (ruff-vscode), 'Astral Software Inc.' (ruff), '@eifinger (from package.json), astral-sh org' (setup-uv), 'Astral Software Inc.' (uv) | low | Verify and resolve | audits/ruff-pre-commit.md, audits/ruff-vscode.md, audits/ruff.md, audits/setup-uv.md, audits/uv.md |
| C-004 | ruff | ruff: Package Details mentions Docker Hub but Artifacts only reference GHCR | low | Verify and resolve | audits/ruff.md |
| C-005 | ruff, uv | Rust toolchain version differs: 1.94 (ruff), 1.94.0 (uv) | medium | Verify and resolve | audits/ruff.md, audits/uv.md |
| C-006 | python-build-standalone, ruff-vscode, uv | Target 'linux' deployed by different CD systems: github actions (python-build-standalone, ruff-vscode), cargo-dist (uv) | low | Verify and resolve | audits/python-build-standalone.md, audits/ruff-vscode.md, audits/uv.md |
| C-007 | python-build-standalone, ruff-vscode, setup-uv, uv | Target 'macos' deployed by different CD systems: github actions (python-build-standalone, ruff-vscode, setup-uv), cargo-dist (uv) | low | Verify and resolve | audits/python-build-standalone.md, audits/ruff-vscode.md, audits/setup-uv.md, audits/uv.md |

### Format for detailed entries

For contradictions that need more space:

#### C-NNN: Title

**Contradiction:** What conflicts with what.

**Impact:** What goes wrong or could go wrong because of this.

**Resolution:** Recommended way to resolve it.

**Open questions:** What still needs to be answered before resolving.

---

## Ambiguities

Things that are not outright contradictions but are unclear enough to cause confusion or mistakes.

| ID | Description | Repos Involved | Impact | Suggested Resolution | Source |
|---|---|---|---|---|---|
| A-001 | | | high · medium · low | | |

---

## Not-Yet Contradictions

Suspected inconsistencies, unresolved weirdness, things that may not be proven wrong yet but deserve verification.

This section is especially useful for:

- Items that feel off but lack a second data point to confirm a conflict
- Patterns noticed during audits that warrant a closer look
- Things that may become contradictions as more repos are audited

| ID | Suspicion | Where Noticed | What Would Confirm It | Status | Source |
|---|---|---|---|---|---|
| N-001 | | | | unverified · investigating · confirmed · dismissed | |

---

## Resolved

Contradictions and ambiguities that have been investigated and resolved. Kept here for historical context.

| ID | Description | Resolution | Resolved Date |
|---|---|---|---|
| | | | |
