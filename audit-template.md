# Audit Template

Standardized process and Copilot prompt for per-repo self-audits. This is the repeatable mechanism for generating structured repo audits.

## Pre-Audit Checklist

Before running the prompt:

- [ ] Open the target repo in VS Code with GitHub Copilot Agent mode
- [ ] Check the active branch — is it the prod-deployed branch?
  - Usually `main` or `master`, but not always
  - Check for deployment indicators: Spinnaker config, `triggerable.yaml`, CI/CD pipeline files
  - Note the actual prod branch if it differs from the default branch
- [ ] Confirm you have the latest code pulled
- [ ] Add `audit.md` to your global `.gitignore` if you haven't already

## The Prompt

Copy everything between the fences below and paste it into Copilot Chat in Agent mode.

---

````
You are performing a structured self-audit of this repository. Your goal is to produce a comprehensive Markdown report that captures the identity, purpose, tech stack, deployment, dependencies, configuration, API surface, secrets, and known gaps of this repo.

Inspect the following (where they exist):

- Directory tree (top two levels)
- README or README.md
- go.mod / go.sum
- package.json / package-lock.json
- pyproject.toml / requirements.txt / setup.py
- Dockerfile / docker-compose.yml
- Makefile
- Jenkinsfile
- jules.yaml / jib.yaml
- spinnaker-trigger.yaml / triggerable.yaml
- chart.yaml / values.yaml (Helm)
- main.tf / variables.tf / outputs.tf (Terraform)
- kustomize overlays (kustomization.yaml)
- Main source entry points (e.g., main.go, app.py, index.ts, cmd/)
- CI/CD config (.github/workflows/, .circleci/, buildspec.yml, etc.)
- Any config/ or deploy/ directories

Produce the report in the exact format below. Use "unknown" for any field you cannot determine. Do not guess — mark it unknown and move on.

---

# Audit: <repo-name>

**Date:** YYYY-MM-DD
**Auditor:** Copilot Agent (reviewed by: <human>)
**Branch audited:** <branch>
**Prod branch (if different):** <branch or "same">

## Identity

| Field | Value |
|---|---|
| Repo name | |
| GitHub URL | |
| Owner(s) | |
| Last meaningful commit | |
| Prod status | active · deprecated · disabled · unknown |
| Purpose | |

## Tech Stack

| Field | Value |
|---|---|
| Language(s) | |
| Framework(s) | |
| Build tool(s) | |
| Runtime | |

## Artifacts Produced

| Artifact | Type | Registry | Destination |
|---|---|---|---|
| | | | |

## Deployment

| Field | Value |
|---|---|
| CI system | |
| CD system | |
| Target environment(s) | |
| Pipeline file(s) | |

## Dependencies

### Outbound (what this repo depends on)

| Dependency | Type | Notes |
|---|---|---|
| | | |

### Inbound (what depends on this repo)

| Consumer | Type | Notes |
|---|---|---|
| | | |

## Config / Sources of Truth

Where does this repo get its configuration? List every external config source.

| Config | Source | Notes |
|---|---|---|
| | | |

Examples: AWS account IDs, image tags, feature flags, environment-specific configs, parameter store paths, config maps.

## API Surface

| Endpoint / Interface | Port | Protocol | Auth | Notes |
|---|---|---|---|---|
| | | | | |

## Secrets and Auth

| Secret / Credential | Source | Used For |
|---|---|---|
| | | |

## Known Gaps

List anything concerning, unclear, or missing:

- 
- 
- 

Examples: no README, tests exist but CI does not run them, hard-coded dev account ID, deprecated base image, unclear ownership, stale dependencies.

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors?
- Are there bus factor concerns (single committer, inactive maintainers)?
- Confidence level: high · medium · low · unknown

---

Save this report as `audit.md` in the repo root. Do not commit or push it.
````

---

## Post-Audit Steps

After the Copilot agent produces the report:

1. **Review critically** — Copilot will get things wrong. Read the output and correct obvious errors.
2. **Fill unknowns** — Use your own knowledge or ask teammates to resolve `unknown` entries where possible.
3. **Flag contradictions** — Note anything that conflicts with what other audits or docs claim.
4. **Copy to Master Control Protocol** — Save as `audits/<repo-name>.md` in this repo.
5. **Update inventory** — Set audit status to `complete` in [inventory.md](inventory.md).
6. **Update maps** — If the audit revealed new dependencies, deployment paths, config sources, contradictions, or gaps, update the relevant files in [maps/](maps/).

## Why This Template Works

**Forces branch realism.** It does not assume `main` equals prod. That is a common enterprise failure mode.

**Structured across the right dimensions.** Identity, purpose, tech stack, artifacts, deployment, dependencies, config sources of truth, API surface, secrets, gaps, ownership confidence.

**Uses "unknown" instead of blanks.** Prevents fake certainty. Makes ambiguity visible and trackable.

**Supports local-only first pass.** Having Copilot save `audit.md` locally in the target repo is convenient for review while avoiding pollution of the source repo history.

**Requires human judgment.** The workflow explicitly includes critical reading, error correction, filling unknowns, flagging contradictions, and updating shared maps. This keeps it from becoming low-quality AI sludge.
