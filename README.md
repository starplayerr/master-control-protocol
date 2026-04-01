# Master Control Protocol

A structured memory and reasoning layer for multi-repo platforms. MCP audits repositories, synthesizes cross-cutting findings into platform maps, tracks what it knows and what it doesn't, and uses its own output to improve over time.

## Why

In platforms spanning dozens of repositories, the bottleneck is rarely implementation skill. It's **orientation** — knowing which repo owns a behavior, where configuration actually lives, what depends on what, and what's stale or contradictory.

Traditional documentation is scattered, repo-local, and decays the moment it's written. MCP replaces it with a system that audits repositories programmatically, cross-references findings across the ecosystem, and compounds its understanding with every run.

## What It Does

MCP runs a pipeline:

1. **Discover** — Enumerate repos in a GitHub org, detect types, track metadata
2. **Audit** — Clone each repo, gather context, call an LLM with a type-specific prompt, produce a structured Markdown report
3. **Synthesize** — Cross-reference all audits to build platform maps: dependency graphs, deployment flows, contradictions, stale assumptions, simplification candidates, missing documentation
4. **Analyze history** — Mine git logs for co-change coupling, knowledge silos, hotspots, and temporal patterns
5. **Capture feedback** — After each audit, automatically detect prompt gaps, cross-repo insights, and unknown fields; optionally collect human corrections
6. **Evolve** — Score prompt effectiveness, propose improvements, grade map quality, and track a composite platform understanding score over time

Every step feeds the next. Audits improve maps. Maps reveal what audits miss. Feedback improves prompts. Better prompts produce better audits.

## Current State

Running against [astral-sh](https://github.com/astral-sh) as a live testbed:

| Metric | Value |
|---|---|
| Repos tracked | 10 |
| Audits complete | 7 (70% coverage) |
| Contradictions found | 19 |
| Stale assumptions | 3 |
| Simplification candidates | 7 |
| Prompt completeness | 97.9% (library prompt) |
| Platform understanding score | 55.4% |

The platform understanding score is a composite of audit coverage, prompt effectiveness, map quality, contradiction resolution, and feedback maturity. It goes up as the system learns.

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
