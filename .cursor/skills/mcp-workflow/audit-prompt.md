# Audit Prompt

This is the full prompt used by the `/audit` workflow. The agent reads this file and follows the instructions against the target repository.

---

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
