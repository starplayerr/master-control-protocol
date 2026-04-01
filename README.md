# Master Control Protocol

The architectural memory layer for multi-repo platforms.

Every engineering org rebuilds the same understanding from scratch — which repo owns what, what depends on what, where config actually lives, what's stale, what contradicts what. This knowledge exists in people's heads, scattered docs, and Slack threads. When someone leaves, it leaves with them. When an AI agent needs it, it doesn't exist in any queryable form.

MCP fixes this. It audits repositories programmatically, cross-references findings across the ecosystem, detects contradictions and stale assumptions that no single-repo tool can see, and compounds its understanding with every run. The output is a structured, queryable, continuously maintained memory of how your platform actually works — for both humans and AI agents.

## What It Found

Running against [astral-sh](https://github.com/astral-sh) (ruff, uv, python-build-standalone, and related repos):

| Metric | Value |
|---|---|
| Repos audited | 7 of 10 (70% coverage) |
| Cross-repo contradictions detected | 19 |
| Stale assumptions identified | 3 |
| Simplification candidates | 7 |
| Undocumented co-change couplings | 10 |
| Hotspot files tracked | 43 |
| Low bus-factor repos | 2 |
| Prompt completeness | 97.9% |
| Platform understanding score | 55.4% |

Findings include version skew between ruff and its VS Code extension, undocumented coupling between repos that always change together, ownership mismatches between audit metadata and actual git contributors, and CI/CD template consolidation opportunities across 4 repos. None of these are visible from any single repository.

## What This Is Not

MCP is not a service catalog (Backstage, Cortex), not a code search engine (Sourcegraph), and not an AI coding assistant (Copilot, Cursor). It's the persistent architectural memory that makes all of those tools more effective. Service catalogs track what exists. Code search finds where things are. AI assistants help you write code. MCP tells you — and them — how the platform actually fits together, where it's broken, and what to do about it.

## How It Works

MCP runs four pipelines that feed each other:

**Audit** — Discover repos in a GitHub org, clone them, send context to an LLM with type-specific prompts (infrastructure, service, library, frontend), produce structured Markdown reports. Cache-aware: only re-audits when code or prompts change.

**Synthesize** — Cross-reference all audit reports to build platform maps: dependency graphs, deployment flows, source-of-truth registries, contradiction logs, stale assumption registers, and simplification candidates. This is the layer that doesn't exist anywhere else.

**Analyze history** — Mine git logs across repos for co-change coupling, knowledge silos, change hotspots, bus-factor risks, and temporal patterns. Surfaces dependencies that aren't declared in code.

**Feedback** — Score prompt effectiveness, detect gaps, propose prompt improvements, grade map quality, and track a composite platform understanding score that rises as the system learns.

Every step feeds the next. Audits improve maps. Maps reveal what audits miss. Feedback improves prompts. Better prompts produce better audits.

## Quick Start

```bash
# Clone and set up
git clone https://github.com/starplayerr/master-control-protocol.git
cd master-control-protocol
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your GITHUB_TOKEN and ANTHROPIC_API_KEY

# Discover and audit an entire org
python scripts/run_all.py --org <your-github-org>

# Run cross-repo synthesis
python scripts/synthesize/run_all.py

# Analyze git history for coupling and knowledge silos
python scripts/history/run_all.py

# Run the feedback loop
python scripts/feedback/run_all.py
```

For a single repo:

```bash
python scripts/audit.py --repo https://github.com/org/repo-name
```

## Repo Structure

```
master-control-protocol/
│
├── INVENTORY.md                       Canonical repo catalog and counts
├── PRIORITY_CLONES.md                 Audit queue and sequencing
├── mcp-manifest.json                  Structure, read order, file registry
├── audit-state.json                   Per-repo cache (SHA + prompt hash)
│
├── audits/                            Structured audit reports
│   ├── ruff.md
│   ├── uv.md
│   ├── ruff-pre-commit.md
│   └── ...
│
├── maps/                              Platform synthesis layer
│   ├── dependency-matrix.md
│   ├── deployment-flow.md
│   ├── source-of-truth.md
│   ├── contradictions-and-ambiguities.md
│   ├── stale-assumptions.md
│   ├── candidate-simplifications.md
│   ├── missing-docs.md
│   └── data/                          Machine-readable JSON for each map
│
├── feedback/                          Compounding feedback loop
│   ├── capture-log.jsonl              Append-only knowledge capture log
│   ├── prompt-scores.json             Prompt effectiveness metrics
│   ├── prompt-proposals.md            Auto-generated prompt improvements
│   ├── map-quality.json               Map quality grades (A–F)
│   ├── dashboard.json                 Full dashboard with time-series data
│   └── quality-history.jsonl          Quality trend tracking
│
├── prompts/                           Type-specific audit prompt templates
│   ├── default.md
│   ├── infrastructure.md
│   ├── library.md
│   ├── service.md
│   └── frontend.md
│
├── scripts/                           Automation pipeline
│   ├── discover.py                    GitHub org repo enumeration
│   ├── audit.py                       Single-repo audit runner
│   ├── run_all.py                     Full pipeline orchestrator
│   ├── check_freshness.py             Staleness detection
│   ├── sync_data.py                   Prose ↔ JSON sync
│   ├── query.py                       CLI query over map data
│   ├── mcp_server.py                  FastMCP server for tool access
│   ├── lib/                           Shared library
│   │   ├── config.py                  Paths, env vars, constants
│   │   ├── llm.py                     Anthropic/OpenAI abstraction
│   │   ├── prompts.py                 Prompt loading + auto-selection
│   │   ├── cache.py                   Audit state management
│   │   ├── context.py                 Clone, tree, file reading
│   │   ├── inventory.py               INVENTORY.md parsing
│   │   └── markdown.py                Markdown table utilities
│   ├── synthesize/                    Cross-repo synthesis engine
│   │   ├── run_all.py                 Synthesis orchestrator
│   │   ├── extract.py                 Audit → structured facts
│   │   ├── dependencies.py            Dependency graph builder
│   │   ├── contradictions.py          Contradiction detector
│   │   ├── stale_assumptions.py       Stale assumption scanner
│   │   └── simplifications.py         Simplification finder
│   ├── history/                       Git history analysis
│   │   ├── run_all.py                 History orchestrator
│   │   ├── git_log.py                 Git log fetching
│   │   ├── coupling.py                Co-change coupling analysis
│   │   ├── hotspots.py                Change hotspot detection
│   │   ├── knowledge.py               Knowledge distribution
│   │   ├── temporal.py                Temporal pattern analysis
│   │   └── integrate.py               Merge findings into maps
│   └── feedback/                      Compounding feedback loop
│       ├── run_all.py                 Feedback orchestrator
│       ├── capture.py                 Post-audit knowledge capture
│       ├── prompt_score.py            Prompt effectiveness scoring
│       ├── evolve_prompt.py           Prompt evolution engine
│       ├── map_quality.py             Map quality grading
│       └── dashboard_data.py          Dashboard data generator
│
├── diagrams/                          Mermaid architecture diagrams
└── reports/                           Report templates
```

## The Pipelines

### Audit Pipeline

```
discover.py → audit.py → capture.py
     │             │           │
     ▼             ▼           ▼
discovered.json  audits/    feedback/capture-log.jsonl
                 INVENTORY.md
                 audit-state.json
```

The audit runner auto-selects a prompt based on repo file signatures (Terraform → infrastructure, React → frontend, Cargo.toml → library, Dockerfile → service). After each audit, the capture step automatically detects prompt gaps, cross-repo insights, and fields that remain unknown. Add `--interactive-capture` to be prompted for human feedback.

### Synthesis Pipeline

```
synthesize/run_all.py
     │
     ├── dependencies    → maps/data/dependency-matrix.json
     ├── contradictions  → maps/data/contradictions-and-ambiguities.json
     ├── stale-assumptions → maps/data/stale-assumptions.json
     └── simplifications → maps/data/candidate-simplifications.json
```

Reads all audits, extracts structured facts, cross-references them, and produces the platform maps.

### History Pipeline

```
history/run_all.py
     │
     ├── git_log     → fetch commit histories
     ├── coupling     → maps/data/co-change-coupling.json
     ├── hotspots     → maps/data/hotspots.json
     ├── knowledge    → maps/data/knowledge-distribution.json
     ├── temporal     → maps/data/temporal-patterns.json
     └── integrate    → updates contradictions, missing-docs, stale-assumptions
```

Mines git histories across all audited repos to find undocumented coupling, knowledge silos, and bus-factor risks.

### Feedback Pipeline

```
feedback/run_all.py
     │
     ├── prompt_score    → feedback/prompt-scores.json
     ├── evolve_prompt   → feedback/prompt-proposals.md
     ├── map_quality     → feedback/map-quality.json
     └── dashboard_data  → feedback/dashboard.json
```

Scores prompt effectiveness (completeness, correction rate, gap rate, trend), proposes prompt improvements from accumulated gaps, grades map quality A–F, and produces a dashboard with the composite platform understanding score.

## Cache and Staleness

`audit-state.json` tracks the last-audited commit SHA and prompt hash for each repo. A repo is re-audited when its code changes (new SHA) or the prompt changes (new hash). Prompt evolution proposals, when approved and applied, automatically bump the hash and trigger re-audits of affected repos.

`check_freshness.py` validates all markdown frontmatter, propagates staleness through `depends_on` chains, and reports which files need attention.

## Adapting for Your Platform

MCP is deliberately generalizable. The current data is from the astral-sh ecosystem (ruff, uv, python-build-standalone), but the structure works for any multi-repo platform:

1. Set `GITHUB_TOKEN` and `ANTHROPIC_API_KEY` in `.env`
2. Run `python scripts/run_all.py --org <your-org>`
3. Run `python scripts/synthesize/run_all.py` to build maps
4. Run `python scripts/history/run_all.py` if you have clone access
5. Run `python scripts/feedback/run_all.py` to score and track quality
6. Repeat — each cycle compounds

The more audits you run, the better the prompts get. The more maps you build, the more contradictions surface. The more feedback you capture, the more the system improves itself.
