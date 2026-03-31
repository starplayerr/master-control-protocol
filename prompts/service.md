---
title: "Service Audit Prompt"
role: template
last_updated: 2026-03-31
depends_on: []
freshness: current
scope: per-repo
---

You are performing a structured self-audit of a service repository. This repo likely runs as a deployed application handling requests, processing data, or serving an API.

You will receive the repository's directory tree and the contents of key files. Inspect them carefully.

In addition to the standard audit dimensions, pay special attention to:

- **Endpoints:** All HTTP/gRPC/WebSocket endpoints, ports, protocols
- **Health checks:** Liveness and readiness probes, health endpoints
- **Scaling:** Resource limits, replica counts, autoscaling config, HPA
- **Graceful shutdown:** Signal handling, drain timeout, connection draining
- **Observability:** Logging, metrics, tracing, alerting configuration
- **Runtime config:** Environment variables, config maps, feature flags consumed at runtime

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

## Deployment

| Field | Value |
|---|---|
| CI system | |
| CD system | |
| Target environment(s) | |
| Pipeline file(s) | |

## Service Details

| Field | Value |
|---|---|
| Primary port | |
| Health check endpoint | |
| Readiness probe | |
| Scaling strategy | |
| Replica count | |
| Resource limits | |
| Graceful shutdown | |
| Observability | |

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
