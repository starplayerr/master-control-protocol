---
title: "Audit: ruff"
role: audit
last_updated: 2026-04-01
depends_on: []
freshness: current
scope: per-repo
---

<!-- audit-meta
timestamp: 2026-04-01T00:37:45.400554+00:00
commit_sha: 39c3636bc9c37db2652a0123848949a459e02988
prompt: library
prompt_hash: 7084e42f3ccb
model: claude-sonnet-4-20250514
context_files: 23
context_chars: 99929
-->

# Audit: ruff

**Date:** 2025-01-16
**Auditor:** automated
**Branch audited:** main
**Prod branch (if different):** same

## Identity

| Field | Value |
|---|---|
| Repo name | ruff |
| GitHub URL | https://github.com/astral-sh/ruff |
| Owner(s) | Astral Software Inc. |
| Last meaningful commit | unknown |
| Prod status | active |
| Purpose | An extremely fast Python linter and code formatter, written in Rust |

## Tech Stack

| Field | Value |
|---|---|
| Language(s) | Rust, Python, JavaScript/TypeScript |
| Framework(s) | Maturin, wasm-bindgen, React/Vite |
| Build tool(s) | Cargo, maturin, npm |
| Runtime | Native binary, Python package, WebAssembly |

## Artifacts Produced

| Artifact | Type | Registry | Destination |
|---|---|---|---|
| ruff | Python package | PyPI | pip install ruff |
| ruff | Binary | GitHub Releases | Standalone installers |
| @astral-sh/ruff-wasm-* | npm packages | NPM | JavaScript environments |
| ghcr.io/astral-sh/ruff | Docker image | GHCR | Container registry |

## Package Details

| Field | Value |
|---|---|
| Package name | ruff |
| Registry | PyPI |
| Current version | 0.15.8 |
| Version strategy | Semantic versioning |
| Release frequency | Regular releases |
| Public API surface | CLI binary, Python module, WASM bindings |
| Known consumers | Apache Airflow, Apache Superset, FastAPI, Hugging Face, Pandas, SciPy |
| Breaking change policy | Minor version bumps for breaking changes |

## Deployment

| Field | Value |
|---|---|
| CI system | GitHub Actions |
| CD system | cargo-dist |
| Target environment(s) | PyPI, GitHub Releases, npm, Docker Registry |
| Pipeline file(s) | .github/workflows/release.yml |

## Dependencies

### Outbound (what this repo depends on)

| Dependency | Type | Notes |
|---|---|---|
| Rust toolchain | Build | Version 1.94 specified |
| Python | Build | Python 3.7+ supported |
| cargo-dist | Release | Version 0.31.0 |
| maturin | Build | Python package building |

### Inbound (what depends on this repo)

| Consumer | Type | Notes |
|---|---|---|
| ruff-pre-commit | Git hooks | Pre-commit integration |
| ruff-vscode | Editor extension | VS Code extension |
| ruff-action | GitHub Action | CI integration |
| Major Python projects | Direct usage | Listed in README |

## Config / Sources of Truth

Where does this repo get its configuration? List every external config source.

| Config | Source | Notes |
|---|---|---|
| Cargo.toml | Repository | Rust workspace configuration |
| pyproject.toml | Repository | Python package metadata |
| dist-workspace.toml | Repository | cargo-dist configuration |
| rust-toolchain.toml | Repository | Rust version specification |

## API Surface

| Endpoint / Interface | Port | Protocol | Auth | Notes |
|---|---|---|---|---|
| CLI binary | N/A | Command line | None | Primary interface |
| Python module | N/A | Python import | None | `import ruff` |
| WASM bindings | N/A | JavaScript | None | Web/Node.js usage |
| LSP server | N/A | LSP | None | Editor integration |

## Secrets and Auth

| Secret / Credential | Source | Used For |
|---|---|---|
| GITHUB_TOKEN | GitHub Actions | Release automation |
| ASTRAL_VERSIONS_PAT | Secrets | Version updates |
| ASTRAL_DOCS_PAT | Secrets | Documentation publishing |
| CF_API_TOKEN | Secrets | Playground deployment |
| PyPI trusted publishing | OIDC | PyPI releases |

## Known Gaps

List anything concerning, unclear, or missing:

- No explicit changelog maintenance strategy documented
- Bus factor risk with primary maintainer Charlie Marsh
- Multiple playground applications but unclear deployment strategy coordination
- Complex multi-artifact release pipeline with many moving parts

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors? Cannot verify without recent commits
- Are there bus factor concerns (single committer, inactive maintainers)? Likely bus factor concerns given single author attribution
- Confidence level: medium