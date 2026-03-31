---
title: "Scripts"
role: overview
last_updated: 2026-03-31
freshness: current
scope: platform
---

# Scripts

Automated pipeline for discovering repos, running structured audits, and updating MCP.

## Setup

```bash
# From the repo root
pip install -r requirements.txt

# Copy and fill in your API keys
cp .env.example .env
```

Required environment variables:

| Variable | Required For | Notes |
|---|---|---|
| `GITHUB_TOKEN` | Discovery, cloning private repos | GitHub personal access token with `repo` scope |
| `ANTHROPIC_API_KEY` | Audit (default provider) | From console.anthropic.com |
| `OPENAI_API_KEY` | Audit (if using `--provider openai`) | From platform.openai.com |

## Usage

### Discover repos in an org

```bash
python scripts/discover.py --org <github-org>
```

Outputs `discovered.json` with repo metadata (name, branch, SHA, languages, topics).

Options:
- `--skip-archived / --include-archived` (default: skip)
- `--skip-forks / --include-forks` (default: skip)
- `--min-size <kb>` — filter out tiny repos
- `--diff` — compare against INVENTORY.md and show new/removed repos

### Audit a single repo

```bash
python scripts/audit.py --repo https://github.com/org/repo-name
```

Clones the repo, gathers context, auto-selects a prompt, calls the LLM, and saves the report to `audits/<repo-name>.md`. Updates INVENTORY.md and audit-state.json automatically.

Options:
- `--branch <branch>` — audit a specific branch (default: repo default)
- `--prompt <name>` — override auto-detection (default, infrastructure, library, service, frontend)
- `--provider <anthropic|openai>` — LLM provider (default: anthropic)
- `--model <name>` — specific model
- `--context-budget <chars>` — max context size (default: 100000)
- `--force` — re-audit even if cache says current

### Run the full pipeline

```bash
python scripts/run_all.py --org <github-org>
```

End-to-end: discovers repos, checks cache, audits stale/new repos in parallel, updates inventory.

Options:
- `--repos <url1,url2>` — audit explicit repos instead of discovering
- `--concurrency <n>` — parallel workers (default: 3)
- `--provider`, `--model` — LLM configuration
- `--force` — ignore cache, re-audit everything
- `--dry-run` — discover and check cache without actually auditing

## Architecture

```
scripts/
├── discover.py          CLI: repo discovery
├── audit.py             CLI: single-repo audit
├── run_all.py           CLI: full pipeline orchestrator
└── lib/
    ├── config.py        Paths, env vars, constants
    ├── context.py       Clone, tree, file reading with budget
    ├── llm.py           Anthropic/OpenAI abstraction
    ├── prompts.py       Prompt loading + auto-selection
    ├── cache.py         audit-state.json management
    └── inventory.py     INVENTORY.md parsing + updates
```

## Prompt Auto-Selection

The audit runner detects repo type from file signatures:

| Signal | Prompt |
|---|---|
| `*.tf` files, Helm charts, Kustomize | `infrastructure` |
| `package.json` with React/Vue/Angular/Next | `frontend` |
| `package.json` with `main`/`bin`, no UI framework | `library` |
| `pyproject.toml`/`setup.py` without Dockerfile | `library` |
| Dockerfile present | `service` |
| Fallback | `default` |

Override with `--prompt <name>` on any audit command.

## Cache Behavior

`audit-state.json` tracks the last-audited commit SHA and prompt hash for each repo. On each run:

- **Both match** → skip (already current)
- **Code changed** (new SHA) → re-audit
- **Prompt changed** (new hash) → re-audit
- **Never audited** → audit

Use `--force` to override the cache.
