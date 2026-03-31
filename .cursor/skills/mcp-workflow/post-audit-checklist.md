# Post-Audit Integration Checklist

This checklist is used by the `/integrate {repo-name}` workflow. The agent reads this file and follows each step to integrate a completed audit into Master Control Protocol.

---

## Prerequisites

- [ ] The audit in `audit.md` has been reviewed by a human
- [ ] Obvious errors have been corrected
- [ ] Unknowns have been filled where possible
- [ ] Contradictions with other audits have been flagged

## Step 1: Copy the Audit

- Copy the reviewed audit to `audits/{repo-name}.md` in MCP
- Preserve the full report content
- Ensure the filename matches the repo name exactly (lowercase, hyphens)

## Step 2: Update INVENTORY.md

- If the repo already has a row, set `Audit Status` to `complete`
- If the repo is not yet in the catalog, add a new row with all available fields
- Update the **Canonical Counts** at the top of the file:
  - Total repos
  - Audited count
  - Coverage percentage
  - Last updated date

## Step 3: Update PRIORITY_CLONES.md

- If the repo appears in the audit queue, set its status to `audited`
- Add a 1-2 sentence outcome summary for the repo
- If the audit revealed new repos that should be prioritized, add them to the queue
- Re-evaluate sequencing if priorities have shifted

## Step 4: Review Maps

Check each map for relevant cross-cutting findings from the audit:

### dependency-matrix.md
- New library/package dependencies?
- New container image producer/consumer relationships?
- New infrastructure flows or remote state references?
- Unexpected or concerning dependencies?

### deployment-flow.md
- New deployment paths or pipeline configurations?
- Branch-to-environment mappings that differ from assumptions?
- Rollback gaps or latency concerns?
- Dual-path deployment problems?

### source-of-truth.md
- New configurable dimensions discovered?
- Split or contested sources of truth?
- Config propagation paths that span multiple repos?
- Does anything override what was previously assumed authoritative?

### contradictions-and-ambiguities.md
- Does this audit conflict with any previous audit or existing documentation?
- Are there ambiguities that this audit partially clarifies?
- Any new not-yet contradictions (suspicious but unconfirmed)?

### stale-assumptions.md
- Deprecated dependencies or base images?
- References to old systems, endpoints, or team names?
- TODOs or FIXMEs older than 12 months?
- Config pointing to decommissioned resources?

### missing-docs.md
- No README or README is a stub?
- Missing runbook or operational docs?
- Undocumented API surface?
- No onboarding guide?
- Missing architecture decision records?

### candidate-simplifications.md
- Duplicated configuration that exists in other repos?
- Dead code or unused features?
- Unnecessary coupling to other repos?
- Services that could be consolidated or replaced?

## Step 5: Flag Diagram Updates

If the audit revealed new dependencies or deployment paths, note which diagrams in `diagrams/` may need updating:
- `dependency-matrix.md`
- `deployment-flow.md`
- `eks-infra-stack.md`

Do not update diagrams automatically — flag them for human review.

## Step 6: Summarize

Report to the user:
- Which files were updated
- What cross-cutting findings were integrated
- What needs human judgment or further investigation
