---
title: "Audit: ruff-pre-commit"
role: audit
last_updated: 2026-03-31
depends_on: []
freshness: current
scope: per-repo
---

<!-- audit-meta
timestamp: 2026-03-31T21:26:22.717222+00:00
commit_sha: c53b915162b475dfc95c73f94219e6f87ace2fca
prompt: library
prompt_hash: 7084e42f3ccb
model: claude-sonnet-4-20250514
context_files: 4
context_chars: 10741
-->

# Audit: ruff-pre-commit

**Date:** 2026-03-31
**Auditor:** automated
**Branch audited:** main
**Prod branch (if different):** same

## Identity

| Field | Value |
|---|---|
| Repo name | ruff-pre-commit |
| GitHub URL | https://github.com/astral-sh/ruff-pre-commit |
| Owner(s) | astral-sh |
| Last meaningful commit | unknown |
| Prod status | active |
| Purpose | Pre-commit hook wrapper for Ruff linter/formatter |

## Tech Stack

| Field | Value |
|---|---|
| Language(s) | Python |
| Framework(s) | pre-commit |
| Build tool(s) | uv |
| Runtime | Python |

## Artifacts Produced

| Artifact | Type | Registry | Destination |
|---|---|---|---|
| pre-commit hook | pre-commit hook | GitHub | pre-commit ecosystem |

## Package Details

| Field | Value |
|---|---|
| Package name | ruff-pre-commit |
| Registry | GitHub (pre-commit hooks) |
| Current version | v0.15.8 |
| Version strategy | mirrors Ruff version |
| Release frequency | automated on Ruff releases |
| Public API surface | ruff-check and ruff-format hooks |
| Known consumers | pre-commit users, prek users |
| Breaking change policy | follows Ruff's breaking change policy |

## Deployment

| Field | Value |
|---|---|
| CI system | GitHub Actions |
| CD system | GitHub Actions |
| Target environment(s) | GitHub repository |
| Pipeline file(s) | .github/workflows/main.yml |

## Dependencies

### Outbound (what this repo depends on)

| Dependency | Type | Notes |
|---|---|---|
| ruff==0.15.8 | Python package | Pinned to specific version |
| uv | Build tool | For Python package management |

### Inbound (what depends on this repo)

| Consumer | Type | Notes |
|---|---|---|
| pre-commit users | pre-commit hook | Anyone using ruff via pre-commit |
| prek users | prek hook | Anyone using ruff via prek |

## Config / Sources of Truth

Where does this repo get its configuration? List every external config source.

| Config | Source | Notes |
|---|---|---|
| Ruff version | PyPI releases | Automated mirroring via repository_dispatch |
| Hook definitions | .pre-commit-hooks.yaml | Defines available hooks |
| Build config | pyproject.toml | Python project configuration |

## API Surface

| Endpoint / Interface | Port | Protocol | Auth | Notes |
|---|---|---|---|---|
| ruff-check hook | N/A | pre-commit | none | Linting hook |
| ruff-format hook | N/A | pre-commit | none | Formatting hook |

## Secrets and Auth

| Secret / Credential | Source | Used For |
|---|---|---|
| GITHUB_TOKEN | GitHub Actions | Creating releases and pushing commits |

## Known Gaps

List anything concerning, unclear, or missing:

- No visible changelog or release notes beyond GitHub releases
- Automated mirroring could fail if PyPI webhook system changes
- No explicit versioning strategy documented beyond following Ruff
- No test suite visible for the hooks themselves
- Bus factor concern - appears to be fully automated with minimal human oversight

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors? unknown
- Are there bus factor concerns (single committer, inactive maintainers)? medium concern - highly automated system
- Confidence level: medium