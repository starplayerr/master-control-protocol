# Source of Truth

For each configurable dimension, where does the canonical value actually live?

This is one of the most operationally useful maps because complex systems often have multiple places where the "same" value appears, but only one of them is actually authoritative.

This file identifies:

- The primary source of truth
- Split or duplicated sources
- Override paths
- What wins at runtime

---

## Source of Truth Registry

| Dimension | Where Config Lives | Split? | What Wins at Runtime | Notes | Source |
|---|---|---|---|---|---|
| AWS account IDs | | | | | |
| Container image tags | | | | | |
| Python package versions | | | | | |
| EKS cluster endpoints / names | | | | | |
| Service / application IDs | | | | | |
| Auth config (IAM / OIDC) | | | | | |
| DNS / URL routing | | | | | |
| Environment definitions (dev/test/UAT/prod) | | | | | |
| Feature flags | | | | | |
| Secrets / credentials | | | | | |

> Add rows as audits reveal new configurable dimensions.

---

## Contested Sources of Truth

Cases where multiple repos or systems claim to own the same value.

| Dimension | Claimed By | Actual Authority | Resolution | Source |
|---|---|---|---|---|
| | | | | |

> When you find a contested source of truth during an audit, add it here **and** in [contradictions-and-ambiguities.md](contradictions-and-ambiguities.md).

---

## Config Propagation Paths

How do configuration values flow through the system?

| Value | Origin | Propagation Path | Destination | Notes |
|---|---|---|---|---|
| | | | | |

Example: An image tag is set in repo A's Helm values, consumed by repo B's Kustomize overlay, and ultimately deployed to an EKS cluster managed by repo C.

---

## Domain Pattern Inventory

| Domain Pattern | Owner | Purpose | Notes |
|---|---|---|---|
| | | | |

## Service Source Mappings

| Service | Primary Source | Backup / Override | Notes |
|---|---|---|---|
| | | | |

---

## Key Findings

- 

## Major Gaps

- 

---

**Last updated:** —
**Audited repos incorporated:** —
