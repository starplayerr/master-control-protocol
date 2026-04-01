---
title: "Inventory"
role: catalog
last_updated: 2026-03-31
depends_on:
  - audits/*
freshness: draft
scope: platform
---

# Inventory

Full catalog of repositories and audit state. This is the canonical tracking table for the platform.

## Canonical Counts

| Metric | Value |
|---|---|
| Total repos | 0 |
| Audited | 0 |
| Coverage | 0% |
| Last updated | — |

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
| | | | | | | | |

> Add repos here as you discover and audit them. Run `python scripts/discover.py --org <your-org>` to populate automatically.
