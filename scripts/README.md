---
title: "Scripts"
role: overview
last_updated: 2026-04-01
freshness: current
scope: platform
---

# Scripts

Automated pipeline for discovering repos, running structured audits, synthesizing cross-repo maps, analyzing git history, and running the compounding feedback loop.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in GITHUB_TOKEN and ANTHROPIC_API_KEY (minimum)
```

| Variable | Required For | Notes |
|---|---|---|
| `GITHUB_TOKEN` | Discovery, cloning | GitHub PAT with `repo` scope |
| `ANTHROPIC_API_KEY` | Audits (default provider) | From console.anthropic.com |
| `OPENAI_API_KEY` | Audits (if using `--provider openai`) | From platform.openai.com |

## Commands

### Discover repos

```bash
python scripts/discover.py --org <github-org>
```

Outputs `discovered.json` with repo metadata. Options: `--skip-archived`, `--skip-forks`, `--min-size <kb>`, `--diff` (compare against INVENTORY.md).

### Audit a single repo

```bash
python scripts/audit.py --repo https://github.com/org/repo-name
# or, if already cloned locally
python scripts/audit.py --local-path /path/to/repo
```

With `--repo`, MCP clones the repository first. With `--local-path`, MCP audits an existing local git checkout and skips cloning. In both cases it gathers context, auto-selects a prompt, calls the LLM, saves the report to `audits/<repo-name>.md`, updates INVENTORY.md and audit-state.json, then runs automated feedback capture.

**Prompts:** `prompts/default.md` and the type-specific files (`library.md`, `service.md`, …) are for the **automated** pipeline. For a **deep manual audit** with a human plus a high-context model, use [prompts/deep-audit.md](../prompts/deep-audit.md) instead.

Options:
- `--branch <branch>` — audit a specific branch
- `--local-path <dir>` — audit an existing local git repository path (alternative to `--repo`)
- `--prompt <name>` — override auto-detection (default, infrastructure, library, service, frontend)
- `--provider <anthropic|openai>` — LLM provider
- `--model <name>` — specific model
- `--context-budget <chars>` — max context size (default: 100,000)
- `--force` — re-audit even if cache says current
- `--interactive-capture` — prompt for manual feedback after audit

### Run the full audit pipeline

```bash
python scripts/run_all.py --org <github-org>
```

End-to-end: discovers repos, checks cache, audits stale/new repos in parallel, updates inventory. Each audit automatically captures feedback.

Options: `--repos <url1,url2>`, `--concurrency <n>`, `--provider`, `--model`, `--force`, `--dry-run`.

### Run cross-repo synthesis

```bash
python scripts/synthesize/run_all.py
```

Reads all audits, extracts structured facts, and builds platform maps: dependency graph, contradictions, stale assumptions, simplification candidates.

Options: `--only <name>` (dependencies, contradictions, stale-assumptions, simplifications), `--dry-run`.

### Run git history analysis

```bash
python scripts/history/run_all.py
```

Fetches git logs from all audited repos and analyzes co-change coupling, hotspots, knowledge distribution, and temporal patterns. Integrates findings into the contradiction, missing-docs, and stale-assumption maps.

### Run the feedback loop

```bash
python scripts/feedback/run_all.py
```

Scores prompt effectiveness, generates prompt evolution proposals, grades map quality, and produces a dashboard with the platform understanding score.

Options: `--only <name>` (prompt-scores, evolve-prompts, map-quality, dashboard), `--use-llm` (LLM-based gap clustering), `--dry-run`.

### Run post-audit capture manually

```bash
python scripts/feedback/capture.py --audit audits/repo-name.md
python scripts/feedback/capture.py --audit audits/repo-name.md --interactive
```

Runs automated capture (detects prompt gaps, cross-repo insights, unknown resolutions) and optionally prompts for human feedback.

### Check freshness

```bash
python scripts/check_freshness.py
python scripts/check_freshness.py --fix
```

Validates frontmatter freshness across all markdown files and propagates staleness through dependency chains.

### Query map data

```bash
python scripts/query.py contradictions --repo ruff
python scripts/query.py dependencies --repo uv
```

CLI interface for querying structured map data.

## Architecture

```
scripts/
├── discover.py              GitHub org repo enumeration
├── audit.py                 Single-repo audit runner + capture hook
├── run_all.py               Full pipeline orchestrator
├── check_freshness.py       Staleness detection
├── sync_data.py             Prose ↔ JSON sync
├── query.py                 CLI query over map data
├── mcp_server.py            FastMCP server (stdio)
├── lib/                     Shared library
│   ├── config.py            Paths, env vars, constants
│   ├── context.py           Clone, tree, file reading with budget
│   ├── llm.py               Anthropic/OpenAI abstraction
│   ├── prompts.py           Prompt loading + auto-selection
│   ├── cache.py             audit-state.json management
│   ├── inventory.py         INVENTORY.md parsing + updates
│   └── markdown.py          Markdown table utilities
├── synthesize/              Cross-repo synthesis engine
│   ├── run_all.py           Orchestrator
│   ├── extract.py           Audit → structured AuditFacts
│   ├── dependencies.py      Dependency graph builder
│   ├── contradictions.py    Contradiction detector
│   ├── stale_assumptions.py Stale assumption scanner
│   └── simplifications.py   Simplification candidate finder
├── history/                 Git history analysis
│   ├── run_all.py           Orchestrator
│   ├── git_log.py           Git log fetching
│   ├── coupling.py          Co-change coupling
│   ├── hotspots.py          Change hotspots
│   ├── knowledge.py         Knowledge distribution
│   ├── temporal.py          Temporal patterns
│   └── integrate.py         Merge findings into maps
└── feedback/                Compounding feedback loop
    ├── run_all.py           Orchestrator
    ├── capture.py           Post-audit knowledge capture
    ├── prompt_score.py      Prompt effectiveness scoring
    ├── evolve_prompt.py     Prompt evolution engine
    ├── map_quality.py       Map quality grading (A–F)
    └── dashboard_data.py    Dashboard data generator
```

## Prompt Auto-Selection

The audit runner detects repo type from file signatures:

| Signal | Prompt |
|---|---|
| `*.tf`, Helm charts, Kustomize | `infrastructure` |
| `package.json` with React/Vue/Angular/Next | `frontend` |
| `package.json` with `main`/`bin`, no UI framework | `library` |
| `Cargo.toml` | `library` |
| `pyproject.toml`/`setup.py` without Dockerfile | `library` |
| Dockerfile present | `service` |
| Fallback | `default` |

Override with `--prompt <name>` on any audit command.

## Cache Behavior

`audit-state.json` tracks the last-audited commit SHA and prompt hash for each repo:

- **Both match** → skip (already current)
- **Code changed** (new SHA) → re-audit
- **Prompt changed** (new hash) → re-audit
- **Never audited** → audit

Prompt evolution proposals, when applied, bump the prompt hash and trigger re-audits of all repos that used that prompt variant.
