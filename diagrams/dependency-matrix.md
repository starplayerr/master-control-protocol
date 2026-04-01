---
title: "Dependency Matrix"
role: diagram
last_updated: 2026-03-31
depends_on:
  - maps/data/dependency-matrix.json
freshness: draft
scope: platform
---

# Dependency Matrix Diagram

```mermaid
flowchart TD
    repo_a["repo-a"]
    repo_b["repo-b"]
    repo_c["repo-c"]
    repo_a -->|"library"| repo_b
    repo_b -->|"container image"| repo_c
```

> Replace the placeholder nodes above with actual repos and dependencies discovered through audits.

## High-Risk Nodes

| Repo | Dependents | Risk |
|---|---|---|
| | | |
