---
title: "Inventory"
role: catalog
last_updated: 2026-03-31
depends_on:
  - audits/*
freshness: current
scope: platform
---

# Inventory

Full catalog of repositories and audit state. This is the canonical tracking table for the platform.

## Canonical Counts

| Metric | Value |
|---|---|
| Total repos | 10 |
| Audited | 7 |
| Coverage | 70% |
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
| _example-eks-cluster_ | EKS | _Main EKS cluster definitions_ | _platform-team_ | _Terraform, Go_ | _active_ | _not started_ | no longer in org |
| _example-sagemaker-pipelines_ | SageMaker | _ML training pipeline orchestration_ | _ml-team_ | _Python_ | _active_ | _not started_ | no longer in org |
| _example-jupyter-extension_ | Jupyter | _Custom Jupyter notebook extension_ | _tools-team_ | _TypeScript_ | _active_ | _not started_ | no longer in org |
| master-control-protocol | — | A documentation-first platform audit hub for mapping, auditing, and reasoning about multi-repo technical ecosystems | unknown | Markdown | unknown | complete | no longer in org |
| ruff-pre-commit | — | Pre-commit hook wrapper for Ruff linter/formatter | astral-sh | Python | active | complete | — |
| uv | — | An extremely fast Python package and project manager, written in Rust | Astral Software Inc. | Rust, Python | active | complete | — |
| python-build-standalone | — | Produces standalone, highly-redistributable builds of Python | Gregory Szorc <gregory.szorc@gmail.com> | Python, Rust, Shell | active | complete | — |
| setup-uv | — | GitHub Action to install and configure uv (Python package manager) in CI workflows | @eifinger (from package.json), astral-sh org | TypeScript | active | complete | — |
| ruff | — | An extremely fast Python linter and code formatter, written in Rust | Astral Software Inc. | Rust, Python, TypeScript, JavaScript | active | complete | — |
| ruff-vscode | — | Visual Studio Code extension for Ruff Python linter and formatter | astral-sh | TypeScript, Python | active | complete | — |

> Replace the italic example rows above with real repos as you begin inventorying.
