# Inventory

Full catalog of repositories and audit state. This is the canonical tracking table for the platform.

## Canonical Counts

| Metric | Value |
|---|---|
| Total repos | 4 |
| Audited | 1 |
| Coverage | 25% |
| Last updated | 2026-03-31 |

## How to Use

- Add repos as you discover them during audits or exploration.
- Update `Audit Status` after completing an audit via `/integrate`.
- Use this table to track coverage and identify gaps.

## Fields

| Field | Description |
|---|---|
| **Repo** | Repository name (links to GitHub where available) |
| **Surface** | Functional domain this repo belongs to (e.g., EKS, SageMaker, Jupyter, SDK, GPU) |
| **Purpose** | One-line description of what the repo does |
| **Owner** | Team or individual listed as owner |
| **Tech** | Primary languages / frameworks |
| **Prod Status** | `active` · `deprecated` · `unknown` · `disabled` |
| **Audit Status** | `not started` · `in progress` · `complete` · `needs update` |
| **Notes** | Anything notable discovered so far |

## Repository Catalog

| Repo | Surface | Purpose | Owner | Tech | Prod Status | Audit Status | Notes |
|---|---|---|---|---|---|---|---|
| _example-eks-cluster_ | EKS | _Main EKS cluster definitions_ | _platform-team_ | _Terraform, Go_ | _active_ | _not started_ | — |
| _example-sagemaker-pipelines_ | SageMaker | _ML training pipeline orchestration_ | _ml-team_ | _Python_ | _active_ | _not started_ | — |
| _example-jupyter-extension_ | Jupyter | _Custom Jupyter notebook extension_ | _tools-team_ | _TypeScript_ | _active_ | _not started_ | — |
| master-control-protocol | — | A documentation-first platform audit hub for mapping, auditing, and reasoning about multi-repo technical ecosystems | unknown | Markdown | unknown | complete | — |

> Replace the italic example rows above with real repos as you begin inventorying.
