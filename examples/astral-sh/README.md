# Example: astral-sh

This is a complete sample run of Master Control Protocol against the [astral-sh](https://github.com/astral-sh) GitHub organization.

## What's Here

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

## Repos Audited

- [ruff](audits/ruff.md) — Python linter and formatter (Rust)
- [uv](audits/uv.md) — Python package manager (Rust)
- [python-build-standalone](audits/python-build-standalone.md) — Standalone Python builds
- [ruff-pre-commit](audits/ruff-pre-commit.md) — Pre-commit hook for Ruff
- [ruff-vscode](audits/ruff-vscode.md) — VS Code extension for Ruff
- [setup-uv](audits/setup-uv.md) — GitHub Action for uv

## Key Findings

- Version skew between ruff and its VS Code extension
- Undocumented coupling between repos that always change together
- Ownership mismatches between audit metadata and actual git contributors
- CI/CD template consolidation opportunities across 4 repos
- 3 stale assumptions requiring verification

## Structure

```
astral-sh/
├── INVENTORY.md            Populated repo catalog
├── audit-state.json        Cache state for all 7 audits
├── discovered.json         GitHub org discovery results
├── audits/                 7 structured audit reports
├── maps/                   Platform synthesis maps (with data)
│   └── data/               Machine-readable JSON
├── feedback/               Feedback loop data and dashboard
├── diagrams/               Mermaid dependency diagram
└── facts-cache/            Extracted facts per repo
```

## How This Was Generated

1. `python scripts/discover.py --org astral-sh` — discovered 40+ repos
2. `python scripts/run_all.py --org astral-sh` — audited the top 7
3. `python scripts/synthesize/run_all.py` — built cross-repo maps
4. `python scripts/history/run_all.py` — mined git history
5. `python scripts/feedback/run_all.py` — scored prompts and graded maps

Total wall time: ~45 minutes. All automated except for human review of audit reports.
