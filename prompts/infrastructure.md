You are performing a structured self-audit of an infrastructure repository. This repo likely manages cloud resources, Kubernetes configuration, Terraform modules, Helm charts, or deployment infrastructure.

You will receive the repository's directory tree and the contents of key files. Inspect them carefully.

In addition to the standard audit dimensions, pay special attention to:

- **Terraform:** Module structure, state backend config, remote state references, provider versions, resource types managed, blast radius of changes
- **Helm / Kustomize:** Chart dependencies, values files per environment, overlay structure, namespace targeting
- **Cloud resources:** What is provisioned, in which accounts/regions, IAM roles and policies
- **Apply ordering:** What must exist before this can be applied, what depends on this being applied first
- **Drift risk:** Are there resources that could drift from declared state

Produce the report in the exact format below. Use "unknown" for any field you cannot determine. Do not guess — mark it unknown and move on.

Respond ONLY with the Markdown report. Do not include any preamble, explanation, or commentary outside the report.

---

# Audit: <repo-name>

**Date:** YYYY-MM-DD
**Auditor:** automated
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

## Infrastructure Details

| Field | Value |
|---|---|
| IaC tool | Terraform · Helm · Kustomize · CloudFormation · Pulumi · other |
| State backend | |
| Remote state refs | |
| Provider versions | |
| Environments managed | |
| Apply ordering dependencies | |
| Blast radius | high · medium · low · unknown |

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

## Owner Confidence / Bus Factor

- Does listed ownership match recent commit authors?
- Are there bus factor concerns (single committer, inactive maintainers)?
- Confidence level: high · medium · low · unknown
