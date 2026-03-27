# Workflow: Running a Self-Audit on a New Repo

Visual rendering of the audit process described in [audit-template.md](../audit-template.md).

```mermaid
flowchart TD
    start([Start]) --> open[Open target repo in VS Code]
    open --> branch{Check active branch}
    branch -->|Is prod branch| deploy_check[Check deployment indicators]
    branch -->|Not prod branch| switch[Switch to prod branch]
    switch --> deploy_check

    deploy_check --> copy[Copy prompt from audit-template.md]
    copy --> paste[Paste into Copilot Chat — Agent mode]
    paste --> run[Copilot explores repo and generates report]
    run --> save_local[Copilot saves audit.md in repo root]

    save_local --> review{Human review}
    review --> correct[Correct obvious errors]
    correct --> fill[Fill in unknowns where possible]
    fill --> flag[Flag contradictions]

    flag --> copy_mcp[Copy to audits/repo-name.md in MCP]
    copy_mcp --> update_inv[Update inventory.md audit status]
    update_inv --> cross{New map-level findings?}

    cross -->|Yes| update_dep[Update dependency matrix]
    update_dep --> update_deploy[Update deployment flow]
    update_deploy --> update_sot[Update source of truth]
    update_sot --> update_contra[Update contradictions]
    update_contra --> update_other[Update other maps as needed]
    update_other --> done([Done])

    cross -->|No| done
```

## The Compounding Loop

```mermaid
flowchart LR
    audit[Audit Repo] --> save[Save Findings]
    save --> inventory[Update Inventory]
    inventory --> maps[Update Shared Maps]
    maps --> understanding[Platform Understanding Improves]
    understanding -->|Next audit is better| audit
```

Each audit feeds the shared model. The shared model makes the next audit more effective. This is the core value loop of Master Control Protocol.
