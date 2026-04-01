---
title: "Audit: setup-uv"
role: audit
last_updated: 2026-03-31
depends_on: []
freshness: current
scope: per-repo
---

<!-- audit-meta
timestamp: 2026-03-31T21:27:58.519697+00:00
commit_sha: d7fe1a5a186096cccdd5fa2252d223b54fa53a72
prompt: library
prompt_hash: 7084e42f3ccb
model: claude-sonnet-4-20250514
context_files: 7
context_chars: 39303
-->

# Audit: setup-uv

**Date:** 2025-01-01
**Auditor:** automated
**Branch audited:** main
**Prod branch (if different):** same

## Identity

| Field | Value |
|---|---|
| Repo name | setup-uv |
| GitHub URL | https://github.com/astral-sh/setup-uv |
| Owner(s) | @eifinger (from package.json), astral-sh org |
| Last meaningful commit | unknown |
| Prod status | active |
| Purpose | GitHub Action to install and configure uv (Python package manager) in CI workflows |

## Tech Stack

| Field | Value |
|---|---|
| Language(s) | TypeScript |
| Framework(s) | GitHub Actions |
| Build tool(s) | npm, esbuild, @vercel/ncc |
| Runtime | Node.js |

## Artifacts Produced

| Artifact | Type | Registry | Destination |
|---|---|---|---|
| GitHub Action | composite action | GitHub Actions Marketplace | GitHub Actions workflows |
| Compiled bundles | JavaScript bundles | dist/ directory | GitHub repository |

## Package Details

| Field | Value |
|---|---|
| Package name | setup-uv |
| Registry | GitHub Actions Marketplace |
| Current version | v8.0.0 |
| Version strategy | semver with git tags |
| Release frequency | unknown |
| Public API surface | GitHub Action inputs/outputs (version, python-version, enable-cache, etc.) |
| Known consumers | GitHub Actions workflows using astral-sh/setup-uv |
| Breaking change policy | unknown |

## Deployment

| Field | Value |
|---|---|
| CI system | GitHub Actions |
| CD system | GitHub Actions |
| Target environment(s) | GitHub Actions runners (ubuntu, macos, windows) |
| Pipeline file(s) | .github/workflows/test.yml, .github/workflows/codeql-analysis.yml, .github/workflows/update-known-checksums.yml, .github/workflows/release-drafter.yml |

## Dependencies

### Outbound (what this repo depends on)

| Dependency | Type | Notes |
|---|---|---|
| @actions/cache | runtime | GitHub Actions cache functionality |
| @actions/core | runtime | Core GitHub Actions toolkit |
| @actions/exec | runtime | Execute commands in actions |
| @actions/glob | runtime | File globbing utilities |
| @actions/io | runtime | File I/O utilities |
| @actions/tool-cache | runtime | Tool caching functionality |
| @renovatebot/pep440 | runtime | Python version parsing |
| smol-toml | runtime | TOML file parsing |
| undici | runtime | HTTP client |

### Inbound (what depends on this repo)

| Consumer | Type | Notes |
|---|---|---|
| GitHub Actions workflows | action consumer | Any workflow using astral-sh/setup-uv |
| astral-sh/uv users | indirect | Workflows that need uv installation |

## Config / Sources of Truth

Where does this repo get its configuration? List every external config source.

| Config | Source | Notes |
|---|---|---|
| Action metadata | action.yml | Defines inputs, outputs, and action behavior |
| uv versions | astral-sh/versions manifest | Remote manifest for available uv versions |
| GitHub releases | astral-sh/uv releases | Downloads uv binaries from GitHub |
| Project configs | uv.toml, pyproject.toml | User project files for version detection |

## API Surface

| Endpoint / Interface | Port | Protocol | Auth | Notes |
|---|---|---|---|---|
| GitHub Action inputs | N/A | GitHub Actions | GitHub token | version, python-version, enable-cache, etc. |
| GitHub Action outputs | N/A | GitHub Actions | N/A | uv-version, uv-path, cache-hit, etc. |

## Secrets and Auth

| Secret / Credential | Source | Used For |
|---|---|---|
| GITHUB_TOKEN | GitHub Actions | Downloading uv from GitHub releases |

## Known Gaps

List anything concerning, unclear, or missing:

- No explicit versioning policy or changelog mentioned
- Release frequency unknown
- Breaking change policy not documented
- No explicit documentation of supported uv version ranges
- Bus factor concerns - single author listed in package.json

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors? unknown - cannot see recent commits
- Are there bus factor concerns (single committer, inactive maintainers)? potentially - only @eifinger listed as author
- Confidence level: medium