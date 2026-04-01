---
title: "Audit: python-build-standalone"
role: audit
last_updated: 2026-03-31
depends_on: []
freshness: current
scope: per-repo
---

<!-- audit-meta
timestamp: 2026-03-31T21:26:58.919546+00:00
commit_sha: 0b479dfdfd836c7c8bd2c469f27c245a0ad0ef91
prompt: library
prompt_hash: 7084e42f3ccb
model: claude-sonnet-4-20250514
context_files: 11
context_chars: 59624
-->

# Audit: python-build-standalone

**Date:** 2026-03-31
**Auditor:** automated
**Branch audited:** unknown
**Prod branch (if different):** unknown

## Identity

| Field | Value |
|---|---|
| Repo name | python-build-standalone |
| GitHub URL | unknown |
| Owner(s) | Gregory Szorc <gregory.szorc@gmail.com> |
| Last meaningful commit | unknown |
| Prod status | active |
| Purpose | Produces standalone, highly-redistributable builds of Python |

## Tech Stack

| Field | Value |
|---|---|
| Language(s) | Python, Rust, Shell |
| Framework(s) | unknown |
| Build tool(s) | Cargo, uv, Docker, Makefiles |
| Runtime | Docker containers, GitHub Actions |

## Artifacts Produced

| Artifact | Type | Registry | Destination |
|---|---|---|---|
| python-build-standalone | Python package | PyPI | PyPI registry |
| pythonbuild | Rust binary | GitHub Releases | GitHub releases |
| Python distributions | Standalone builds | GitHub Releases | GitHub releases |
| Docker images | Container images | GitHub Container Registry | ghcr.io |

## Package Details

| Field | Value |
|---|---|
| Package name | python-build-standalone |
| Registry | PyPI, GitHub Releases |
| Current version | 0.1.0 |
| Version strategy | semver |
| Release frequency | unknown |
| Public API surface | Python build tooling, Rust CLI tools |
| Known consumers | unknown |
| Breaking change policy | unknown |

## Deployment

| Field | Value |
|---|---|
| CI system | GitHub Actions |
| CD system | GitHub Actions |
| Target environment(s) | Linux, macOS, Windows |
| Pipeline file(s) | .github/workflows/linux.yml, .github/workflows/macos.yml, .github/workflows/windows.yml, .github/workflows/release.yml |

## Dependencies

### Outbound (what this repo depends on)

| Dependency | Type | Notes |
|---|---|---|
| boto3 | Python runtime | AWS SDK |
| docker | Python runtime | Docker SDK |
| jinja2 | Python runtime | Template engine |
| anyhow | Rust crate | Error handling |
| clap | Rust crate | CLI parsing |
| octocrab | Rust crate | GitHub API client |

### Inbound (what depends on this repo)

| Consumer | Type | Notes |
|---|---|---|
| unknown | unknown | Consumers of standalone Python builds |

## Config / Sources of Truth

Where does this repo get its configuration? List every external config source.

| Config | Source | Notes |
|---|---|---|
| Build targets | ci-targets.yaml | CI build matrix configuration |
| Runners | ci-runners.yaml | CI runner configuration |
| Extension modules | cpython-unix/extension-modules.yml | Python extension module config |
| Build targets | cpython-unix/targets.yml | Unix build targets |
| Build config | pyproject.toml | Python project configuration |
| Rust config | Cargo.toml | Rust project configuration |

## API Surface

| Endpoint / Interface | Port | Protocol | Auth | Notes |
|---|---|---|---|---|
| pythonbuild CLI | N/A | CLI | None | Rust binary for build operations |
| GitHub API | 443 | HTTPS | Token | Release upload/download |
| Docker API | varies | Docker | None | Container builds |

## Secrets and Auth

| Secret / Credential | Source | Used For |
|---|---|---|
| GITHUB_TOKEN | GitHub Actions | GitHub API access, releases |
| ASTRAL_VERSIONS_PAT | GitHub Secrets | Updating versions repository |
| MIRROR_R2_ACCESS_KEY_ID | GitHub Secrets | R2 storage access |
| MIRROR_R2_SECRET_ACCESS_KEY | GitHub Secrets | R2 storage access |

## Known Gaps

List anything concerning, unclear, or missing:

- No clear versioning strategy visible for releases beyond the 0.1.0 in pyproject.toml
- Bus factor concern: Gregory Szorc appears to be primary/sole maintainer
- No clear documentation of consumer count or downstream impact
- Complex build matrix with many platform/architecture combinations
- Heavy dependency on external services (GitHub, AWS R2)

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors? unknown
- Are there bus factor concerns (single committer, inactive maintainers)? Yes - appears to be primarily maintained by single author
- Confidence level: medium