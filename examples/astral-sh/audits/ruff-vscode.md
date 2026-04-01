---
title: "Audit: ruff-vscode"
role: audit
last_updated: 2026-03-31
depends_on: []
freshness: current
scope: per-repo
---

<!-- audit-meta
timestamp: 2026-03-31T21:29:55.991405+00:00
commit_sha: 99f7409378f28d560bc3feacf4960856090dd5b2
prompt: library
prompt_hash: 7084e42f3ccb
model: claude-sonnet-4-20250514
context_files: 8
context_chars: 48331
-->

# Audit: ruff-vscode

**Date:** 2026-03-31
**Auditor:** automated
**Branch audited:** main
**Prod branch (if different):** same

## Identity

| Field | Value |
|---|---|
| Repo name | ruff-vscode |
| GitHub URL | https://github.com/astral-sh/ruff-vscode |
| Owner(s) | astral-sh |
| Last meaningful commit | unknown |
| Prod status | active |
| Purpose | Visual Studio Code extension for Ruff Python linter and formatter |

## Tech Stack

| Field | Value |
|---|---|
| Language(s) | TypeScript, Python |
| Framework(s) | VS Code Extension API, Language Server Protocol |
| Build tool(s) | webpack, npm, vsce |
| Runtime | Node.js, VS Code |

## Artifacts Produced

| Artifact | Type | Registry | Destination |
|---|---|---|---|
| ruff-*.vsix | VS Code Extension | VS Code Marketplace | marketplace.visualstudio.com |
| ruff-*.vsix | VS Code Extension | OpenVSX Registry | open-vsx.org |

## Package Details

| Field | Value |
|---|---|
| Package name | ruff |
| Registry | VS Code Marketplace, OpenVSX |
| Current version | 2026.38.0 |
| Version strategy | CalVer (YYYY.WW.PATCH) |
| Release frequency | unknown |
| Public API surface | VS Code extension contributions (commands, settings, language support) |
| Known consumers | VS Code users developing Python code |
| Breaking change policy | unknown |

## Deployment

| Field | Value |
|---|---|
| CI system | GitHub Actions |
| CD system | GitHub Actions |
| Target environment(s) | VS Code (multiple platforms: Windows, macOS, Linux, Alpine) |
| Pipeline file(s) | .github/workflows/ci.yaml, .github/workflows/release.yaml |

## Dependencies

### Outbound (what this repo depends on)

| Dependency | Type | Notes |
|---|---|---|
| ms-python.python | VS Code Extension | Required extension dependency |
| ruff==0.15.7 | Python Package | Bundled Ruff binary |
| ruff-lsp==0.0.62 | Python Package | Legacy language server |
| packaging>=23.1 | Python Package | Version parsing utilities |
| Node.js dependencies | Runtime | webpack, vsce, eslint, prettier, etc. |

### Inbound (what depends on this repo)

| Consumer | Type | Notes |
|---|---|---|
| VS Code users | Extension | Python developers using Ruff |
| Python projects | Extension | Linting and formatting integration |

## Config / Sources of Truth

Where does this repo get its configuration? List every external config source.

| Config | Source | Notes |
|---|---|---|
| Extension settings | VS Code settings.json | User/workspace configuration |
| Ruff configuration | pyproject.toml, ruff.toml | Ruff-specific configuration files |
| Build configuration | package.json | Extension metadata and build scripts |
| CI/CD configuration | GitHub Actions | Workflow definitions |

## API Surface

| Endpoint / Interface | Port | Protocol | Auth | Notes |
|---|---|---|---|---|
| VS Code Extension API | N/A | VS Code IPC | N/A | Commands, settings, language features |
| Language Server Protocol | N/A | JSON-RPC | N/A | Communication with ruff-lsp or native server |

## Secrets and Auth

| Secret / Credential | Source | Used For |
|---|---|---|
| MARKETPLACE_TOKEN | GitHub Secrets | Publishing to VS Code Marketplace |
| OPENVSX_TOKEN | GitHub Secrets | Publishing to OpenVSX Registry |

## Known Gaps

List anything concerning, unclear, or missing:

- No visible changelog maintenance (CHANGELOG.md present but content unknown)
- Release frequency and versioning strategy details unclear
- Bus factor concerns with single organization ownership
- Complex multi-platform build process with many moving parts
- Migration path from ruff-lsp to native server ongoing (deprecated settings)
- Multiple registries to maintain (VS Code Marketplace + OpenVSX)

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors? unknown
- Are there bus factor concerns (single committer, inactive maintainers)? potentially - owned by single organization (astral-sh)
- Confidence level: medium