---
title: "Deployment Flow"
role: map
last_updated: 2026-03-31
depends_on:
  - INVENTORY.md
  - audits/*
freshness: draft
scope: platform
---

# Deployment Flow

How a code change propagates from Git push to production for each major platform surface.

The point is to make delivery mechanics visible — not how people think deployment works, but how it actually happens.

See also: [diagrams/deployment-flow.md](../diagrams/deployment-flow.md) for a visual rendering.

---

## Flow Template

Each flow describes how a specific class of change moves through the system:

- **Trigger:** Developer change or Git push event
- **Build / Validation:** CI steps, tests, linting
- **Artifact:** What is produced (image, package, bundle, plan)
- **Deployment:** CD system or orchestrator that pushes to target
- **Downstream Propagation:** What else is affected when this deploys
- **Estimated Latency:** Time from push to running in production
- **Rollback Path:** How to undo a bad deployment
- **Gaps:** Observed weak points, ambiguities, or missing automation

---

## Flows

### Notebook Image Updates

| Step | Detail |
|---|---|
| Trigger | |
| Build / Validation | |
| Artifact | |
| Deployment | |
| Downstream Propagation | |
| Estimated Latency | |
| Rollback Path | |
| Gaps | |

### Package Version Changes

| Step | Detail |
|---|---|
| Trigger | |
| Build / Validation | |
| Artifact | |
| Deployment | |
| Downstream Propagation | |
| Estimated Latency | |
| Rollback Path | |
| Gaps | |

### Infrastructure Changes

| Step | Detail |
|---|---|
| Trigger | |
| Build / Validation | |
| Artifact | |
| Deployment | |
| Downstream Propagation | |
| Estimated Latency | |
| Rollback Path | |
| Gaps | |

### Config Changes

| Step | Detail |
|---|---|
| Trigger | |
| Build / Validation | |
| Artifact | |
| Deployment | |
| Downstream Propagation | |
| Estimated Latency | |
| Rollback Path | |
| Gaps | |

> Add new flow sections as audit findings reveal additional deployment paths.

---

## Deployment Paths by Repo

| Repo | CI System | CD System | Artifact | Target | Pipeline File(s) | Notes | Source |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## Deployment Targets

| Target Environment | Type | Repos That Deploy Here | Notes |
|---|---|---|---|
| | | | |

**Type values:** `EKS cluster` · `SageMaker endpoint` · `Lambda` · `S3` · `ECR` · `other`

## Branch-to-Environment Mapping

| Repo | Branch | Environment | Notes |
|---|---|---|---|
| | | | |

Not all repos follow `main → prod`. Document the actual mapping here.

---

## Concerns

This section is especially useful for identifying:

- Dual-path deployment problems
- Hidden deployment dependencies
- Long propagation delays
- Unclear rollback ownership
- Places where runtime behavior differs from what engineers assume

| Concern | Repos Affected | Impact | Notes |
|---|---|---|---|
| | | | |
