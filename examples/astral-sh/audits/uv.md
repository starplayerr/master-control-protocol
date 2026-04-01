---
title: "Audit: uv"
role: audit
last_updated: 2026-03-31
depends_on: []
freshness: current
scope: per-repo
---

<!-- audit-meta
timestamp: 2026-03-31T21:45:28.120676+00:00
commit_sha: 0c1d0f7c80a621d71df5ed82c2aa562f2d8d70ae
prompt: library
prompt_hash: 7084e42f3ccb
model: claude-sonnet-4-20250514
context_files: 21
context_chars: 99970
-->

# Audit: uv

**Date:** 2026-03-31
**Auditor:** automated
**Branch audited:** main
**Prod branch (if different):** same

## Identity

| Field | Value |
|---|---|
| Repo name | uv |
| GitHub URL | https://github.com/astral-sh/uv |
| Owner(s) | Astral Software Inc. |
| Last meaningful commit | unknown |
| Prod status | active |
| Purpose | An extremely fast Python package and project manager, written in Rust |

## Tech Stack

| Field | Value |
|---|---|
| Language(s) | Rust, Python |
| Framework(s) | Cargo (Rust workspace), maturin (Python bindings) |
| Build tool(s) | Cargo, maturin |
| Runtime | Native binary |

## Artifacts Produced

| Artifact | Type | Registry | Destination |
|---|---|---|---|
| uv | Python wheel | PyPI | https://pypi.org/project/uv/ |
| uv | Binary | GitHub Releases | https://github.com/astral-sh/uv/releases |
| uv-build | Python wheel | PyPI | https://pypi.org/project/uv-build/ |
| uv | Docker image | GHCR | ghcr.io/astral-sh/uv |
| Rust crates | Crate | crates.io | Various uv-* crates |

## Package Details

| Field | Value |
|---|---|
| Package name | uv |
| Registry | PyPI, GitHub Releases, crates.io |
| Current version | 0.11.2 |
| Version strategy | SemVer |
| Release frequency | Regular releases (0.x series) |
| Public API surface | CLI interface, Python module wrapper, Rust library crates |
| Known consumers | Python developers, CI/CD systems |
| Breaking change policy | Preview status, breaking changes allowed in 0.x |

## Deployment

| Field | Value |
|---|---|
| CI system | GitHub Actions |
| CD system | cargo-dist |
| Target environment(s) | Linux, macOS, Windows (multiple architectures) |
| Pipeline file(s) | .github/workflows/release.yml, build-release-binaries.yml |

## Dependencies

### Outbound (what this repo depends on)

| Dependency | Type | Notes |
|---|---|---|
| Rust crates | Build/Runtime | 70+ internal workspace crates, many external deps |
| PubGrub | Runtime | Dependency resolver |
| Cargo toolchain | Build | Rust compilation |
| Python interpreters | Runtime | For testing and validation |
| maturin | Build | Python wheel generation |

### Inbound (what depends on this repo)

| Consumer | Type | Notes |
|---|---|---|
| Python developers | End users | Package/project management |
| CI/CD systems | Automation | GitHub Actions, GitLab CI |
| Other tools | Integration | Poetry, pip replacement scenarios |

## Config / Sources of Truth

Where does this repo get its configuration? List every external config source.

| Config | Source | Notes |
|---|---|---|
| Version | pyproject.toml, Cargo.toml | Multiple files need sync |
| Release config | dist-workspace.toml | cargo-dist configuration |
| CI config | .github/workflows/ | GitHub Actions workflows |
| Rust toolchain | rust-toolchain.toml | Pinned to 1.94.0 |

## API Surface

| Endpoint / Interface | Port | Protocol | Auth | Notes |
|---|---|---|---|---|
| uv CLI | N/A | Process | None | Main binary interface |
| uvx CLI | N/A | Process | None | Tool runner alias |
| Python module | N/A | Python import | None | Wrapper around binary |
| Rust crate APIs | N/A | Library | None | Public Rust interfaces |

## Secrets and Auth

| Secret / Credential | Source | Used For |
|---|---|---|
| GITHUB_TOKEN | GitHub Actions | Release automation, crates.io auth |
| PyPI tokens | GitHub Secrets | Package publishing |
| Signing keys | GitHub Actions | macOS code signing |

## Known Gaps

List anything concerning, unclear, or missing:

- Complex multi-crate workspace with 70+ internal crates may have dependency management overhead
- Version synchronization across pyproject.toml, multiple Cargo.toml files managed by tooling
- Preview/0.x status means breaking changes are expected
- Large binary size concerns mentioned in Dockerfile comments
- Heavy CI matrix across many platforms increases maintenance burden

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors?
- Are there bus factor concerns (single committer, inactive maintainers)?
- Confidence level: unknown