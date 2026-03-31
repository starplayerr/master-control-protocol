---
name: mcp-workflow
description: Run structured platform audits and integrate findings into Master Control Protocol. Use when the user says audit, integrate, repo audit, platform audit, or run audit. Also use when the user wants to integrate audit findings, update the inventory, or update platform maps.
---

# MCP Workflow

Two-phase workflow for auditing repos and integrating findings into Master Control Protocol.

## /audit

Run a structured self-audit of the current repository.

### Steps

1. **Verify branch.** Check the active branch. Determine whether it represents prod-deployed code.
   - Look for deployment indicators: Spinnaker config, `triggerable.yaml`, CI/CD pipeline files, Helm charts, Terraform configs.
   - If the default branch is not the prod branch, note the actual prod branch in the report.
   - Do not assume `main` or `master` equals prod.

2. **Read the audit prompt.** Load the full prompt from [audit-prompt.md](audit-prompt.md) in this skill folder.

3. **Execute the audit.** Follow the prompt instructions exactly. Explore the repo, inspect the listed files and directories, and produce the structured Markdown report using `unknown` for any field that cannot be determined.

4. **Save locally.** Write the report as `audit.md` in the repo root. Do not commit or push it.

5. **Inform the user.** Tell them the audit is complete and that they should review it critically before running `/integrate`.

## /integrate {repo-name}

Integrate a completed audit into Master Control Protocol. Run this from the MCP workspace after reviewing the audit.

### Steps

1. **Read the checklist.** Load [post-audit-checklist.md](post-audit-checklist.md) in this skill folder.

2. **Copy the audit.** Copy the reviewed `audit.md` into `audits/{repo-name}.md` in MCP.

3. **Update INVENTORY.md.** Set the repo's audit status to `complete`. Add a new row if the repo is not yet inventoried. Update canonical counts at the top of the file.

4. **Update PRIORITY_CLONES.md.** If the repo appears in the audit queue, mark it `audited` and add a short outcome summary. If the audit revealed new priority candidates, add them.

5. **Review maps.** For each map in `maps/`, check whether the audit produced relevant cross-cutting findings:
   - `dependency-matrix.md` — new producer/consumer relationships
   - `deployment-flow.md` — new deployment paths, rollback gaps, latency findings
   - `source-of-truth.md` — new config dimensions, contested sources, propagation paths
   - `contradictions-and-ambiguities.md` — conflicts with other audits or docs
   - `stale-assumptions.md` — deprecated, abandoned, or outdated items
   - `missing-docs.md` — documentation gaps discovered
   - `candidate-simplifications.md` — complexity reduction opportunities

6. **Suggest diagram updates.** If new dependencies or deployment paths were found, note which diagrams in `diagrams/` may need updating.

7. **Summarize.** Tell the user what was updated and flag anything that needs their judgment.
