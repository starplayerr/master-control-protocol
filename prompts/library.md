---
title: "Library Audit Prompt"
role: template
last_updated: 2026-03-31
depends_on: []
freshness: current
scope: per-repo
---

You are performing a structured self-audit of a library or package repository. This repo likely publishes a reusable package consumed by other repos or services.

You will receive the repository's directory tree and the contents of key files. Inspect them carefully.

In addition to the standard audit dimensions, pay special attention to:

- **Publishing:** Where is the package published (npm, PyPI, Artifactory, Maven Central, etc.), what version strategy is used (semver, CalVer, etc.)
- **API surface:** Public exports, entry points, backwards compatibility guarantees
- **Consumers:** Who uses this package, how many downstream dependents are there
- **Breaking changes:** What constitutes a breaking change, is there a deprecation policy
- **Versioning:** Current version, release frequency, changelog practices

Produce the report in the exact format below. Use "unknown" for any field you cannot determine. Do not guess — mark it unknown and move on.

Respond ONLY with the Markdown report. Do not include any preamble, explanation, or commentary outside the report.

---

# Audit: <repo-name>

**Date:** YYYY-MM-DD
**Auditor:** automated
**Branch audited:** <branch>
**Prod branch (if different):** <branch or "same">

## Identity

| Field | Value |
|---|---|
| Repo name | |
| GitHub URL | |
| Owner(s) | |
| Last meaningful commit | |
| Prod status | active · deprecated · disabled · unknown |
| Purpose | |

## Tech Stack

| Field | Value |
|---|---|
| Language(s) | |
| Framework(s) | |
| Build tool(s) | |
| Runtime | |

## Artifacts Produced

| Artifact | Type | Registry | Destination |
|---|---|---|---|
| | | | |

## Package Details

| Field | Value |
|---|---|
| Package name | |
| Registry | |
| Current version | |
| Version strategy | |
| Release frequency | |
| Public API surface | |
| Known consumers | |
| Breaking change policy | |

## Deployment

| Field | Value |
|---|---|
| CI system | |
| CD system | |
| Target environment(s) | |
| Pipeline file(s) | |

## Dependencies

### Outbound (what this repo depends on)

| Dependency | Type | Notes |
|---|---|---|
| | | |

### Inbound (what depends on this repo)

| Consumer | Type | Notes |
|---|---|---|
| | | |

## Config / Sources of Truth

Where does this repo get its configuration? List every external config source.

| Config | Source | Notes |
|---|---|---|
| | | |

## API Surface

| Endpoint / Interface | Port | Protocol | Auth | Notes |
|---|---|---|---|---|
| | | | | |

## Secrets and Auth

| Secret / Credential | Source | Used For |
|---|---|---|
| | | |

## Known Gaps

List anything concerning, unclear, or missing:

-
-
-

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors?
- Are there bus factor concerns (single committer, inactive maintainers)?
- Confidence level: high · medium · low · unknown
