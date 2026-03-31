---
title: "Audit: ruff"
role: audit
last_updated: 2026-03-31
depends_on: []
freshness: current
scope: per-repo
---

<!-- audit-meta
timestamp: 2026-03-31T21:44:33.952089+00:00
commit_sha: 39c3636bc9c37db2652a0123848949a459e02988
prompt: library
prompt_hash: 7084e42f3ccb
model: claude-sonnet-4-20250514
context_files: 23
context_chars: 99929
-->

---

# Audit: ruff

**Date:** 2026-03-31
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
| Language(s) | Rust, Python, TypeScript, JavaScript |
| Framework(s) | Maturin (Python binding), PyO3, wasm-bindgen |
| Build tool(s) | Cargo, maturin, npm, wasm-pack |
| Runtime | Native binary, Python wheels, Node.js, Browser (WASM) |

## Artifacts Produced

| Artifact | Type | Registry | Destination |
|---|---|---|---|
| ruff | PyPI package | PyPI | https://pypi.org/project/ruff/ |
| ruff | Native binary | GitHub Releases | Multiple platforms |
| @astral-sh/ruff-wasm-* | npm packages | npm | Web, Node.js, Bundler targets |
| ghcr.io/astral-sh/ruff | Docker image | GitHub Container Registry | Container deployments |

## Package Details

| Field | Value |
|---|---|
| Package name | ruff |
| Registry | PyPI (primary), npm (WASM), Docker Hub, GitHub Releases |
| Current version | 0.15.8 |
| Version strategy | semantic versioning |
| Release frequency | unknown |
| Public API surface | CLI interface, Python module, WASM bindings, LSP server |
| Known consumers | Apache Airflow, Apache Superset, FastAPI, Hugging Face, Pandas, SciPy |
| Breaking change policy | minor version bump for breaking changes |

## Deployment

| Field | Value |
|---|---|
| CI system | GitHub Actions |
| CD system | cargo-dist |
| Target environment(s) | PyPI, npm, GitHub Releases, Docker Registry |
| Pipeline file(s) | .github/workflows/release.yml, .github/workflows/build-*.yml |

## Dependencies

### Outbound (what this repo depends on)

| Dependency | Type | Notes |
|---|---|---|
| Cargo workspace deps | Build dependencies | 50+ Rust crates defined in Cargo.toml |
| PyO3/maturin | Python bindings | For Python package creation |
| wasm-bindgen | WASM bindings | For JavaScript/browser support |
| GitHub Actions | CI/CD | Various marketplace actions |

### Inbound (what depends on this repo)

| Consumer | Type | Notes |
|---|---|---|
| ruff-pre-commit | Git hook | Pre-commit integration |
| ruff-vscode | VS Code extension | Editor integration |
| ruff-action | GitHub Action | CI integration |
| Major Python projects | Runtime dependency | Listed in README testimonials |

## Config / Sources of Truth

Where does this repo get its configuration? List every external config source.

| Config | Source | Notes |
|---|---|---|
| Rust toolchain | rust-toolchain.toml | Rust 1.94 channel |
| Cargo dist | dist-workspace.toml | Release configuration |
| PyPI metadata | pyproject.toml | Python package configuration |
| GitHub secrets | GitHub repository settings | For publishing and deployment |

## API Surface

| Endpoint / Interface | Port | Protocol | Auth | Notes |
|---|---|---|---|---|
| CLI binary | N/A | Command line | None | Primary interface |
| Python module | N/A | Python import | None | importable as `ruff` |
| LSP server | Variable | LSP over stdio/TCP | None | Language server protocol |
| WASM module | N/A | JavaScript/WASM | None | Browser/Node.js integration |

## Secrets and Auth

| Secret / Credential | Source | Used For |
|---|---|---|
| GITHUB_TOKEN | GitHub | Repository access, releases |
| CF_API_TOKEN | GitHub Secrets | Cloudflare Pages deployment |
| RUFF_PRE_COMMIT_PAT | GitHub Secrets | Pre-commit mirror updates |
| ASTRAL_DOCS_PAT | GitHub Secrets | Documentation publishing |
| MIRROR_R2_* | GitHub Secrets | R2 mirror publishing |

## Known Gaps

List anything concerning, unclear, or missing:

- Release frequency not documented in visible files
- Multiple playground deployments (ruff and ty) with separate workflows
- Complex multi-crate workspace with 50+ internal crates
- WASM build process spans multiple targets (web, bundler, nodejs)
- Documentation deployment relies on external repository (astral-sh/docs)

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors? unknown
- Are there bus factor concerns (single committer, inactive maintainers)? unknown
- Confidence level: medium