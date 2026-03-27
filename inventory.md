# Inventory

Central catalog of repositories and audit state. This is the high-level control table for the platform surface.

## How to Use

- Add repos as you discover them during audits or exploration.
- Update `audit status` after completing an audit.
- Mark `priority clone` for repos you plan to audit next.
- Use this table to track coverage and identify gaps.

## Fields

| Field | Description |
|---|---|
| **Repo** | Repository name (links to GitHub where available) |
| **Surface** | Which platform surface this belongs to (see [surfaces.md](surfaces.md)) |
| **Purpose** | One-line description of what the repo does |
| **Owner** | Team or individual listed as owner |
| **Tech** | Primary languages / frameworks |
| **Prod Status** | `active` · `deprecated` · `unknown` · `disabled` |
| **Audit Status** | `not started` · `in progress` · `complete` · `needs update` |
| **Priority Clone** | `yes` · `no` — whether this should be cloned and audited next |
| **Notes** | Anything notable discovered so far |

## Repository Catalog

| Repo | Surface | Purpose | Owner | Tech | Prod Status | Audit Status | Priority Clone | Notes |
|---|---|---|---|---|---|---|---|---|
| _example-eks-cluster_ | EKS | _Main EKS cluster definitions_ | _platform-team_ | _Terraform, Go_ | _active_ | _not started_ | _yes_ | — |
| _example-sagemaker-pipelines_ | SageMaker | _ML training pipeline orchestration_ | _ml-team_ | _Python_ | _active_ | _not started_ | _yes_ | — |
| _example-jupyter-extension_ | Jupyter | _Custom Jupyter notebook extension_ | _tools-team_ | _TypeScript_ | _active_ | _not started_ | _no_ | — |

> Replace the italic example rows above with real repos as you begin inventorying.

## Priority Clones

Repos recommended for immediate audit, in suggested order:

1. _example-eks-cluster_ — foundational infra, high dependency surface
2. _example-sagemaker-pipelines_ — core ML workflow, deployment complexity

> Update this list as audit priorities shift.

## Coverage Summary

| Surface | Total Repos | Audited | Coverage |
|---|---|---|---|
| EKS | — | — | — |
| SageMaker | — | — | — |
| Jupyter | — | — | — |
| SDK | — | — | — |
| GPU Management | — | — | — |

> Fill in as the inventory grows.
