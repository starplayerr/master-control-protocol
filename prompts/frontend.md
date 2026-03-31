You are performing a structured self-audit of a frontend repository. This repo likely builds a web application, UI component library, or client-side bundle.

You will receive the repository's directory tree and the contents of key files. Inspect them carefully.

In addition to the standard audit dimensions, pay special attention to:

- **Build pipeline:** Bundler (webpack, Vite, esbuild, etc.), build output, source maps
- **Bundle:** Output size, code splitting strategy, lazy loading
- **Framework:** React, Vue, Angular, Svelte, Next.js, etc. and version
- **Routing:** Client-side routing, SSR/SSG/CSR strategy
- **State management:** Redux, Zustand, Pinia, Context, etc.
- **Hosting:** CDN, static hosting, SSR server, edge deployment
- **Testing:** Unit tests, integration tests, E2E (Cypress, Playwright)

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

## Frontend Details

| Field | Value |
|---|---|
| Bundler | |
| Rendering strategy | SSR · SSG · CSR · hybrid · unknown |
| Routing | |
| State management | |
| Bundle size | |
| Code splitting | |
| Hosting / CDN | |
| Testing | |

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
