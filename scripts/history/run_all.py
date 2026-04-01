#!/usr/bin/env python3
"""History analysis orchestrator.

Runs all git-history analyzers in the correct order:
  1. Fetch/update clones and extract histories
  2. Coupling analysis (uses histories)
  3. Hotspot detection (uses histories)
  4. Knowledge distribution (uses histories)
  5. Temporal patterns (uses histories)
  6. Integration (reads analyzer outputs, writes to existing maps)

Supports --only to run a single analyzer, and --dry-run to preview.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from history import git_log, coupling, hotspots, knowledge, temporal, integrate


ANALYZERS = {
    "coupling": ("Co-Change Coupling", coupling),
    "hotspots": ("Change Hotspots", hotspots),
    "knowledge": ("Knowledge Distribution", knowledge),
    "temporal": ("Temporal Patterns", temporal),
    "integrate": ("History Integration", integrate),
}

RUN_ORDER = ["coupling", "hotspots", "knowledge", "temporal", "integrate"]


def _print_result(name: str, label: str, result: dict, elapsed: float) -> None:
    print(f"\n  {label}")
    print(f"  {'-' * len(label)}")

    if name == "coupling":
        print(f"    Pairs analyzed: {result.get('total_pairs', 0)}")
        print(f"    Undocumented couplings: {result.get('undocumented_couplings', 0)}")
        print(f"    Top score: {result.get('top_score', 0)}")
    elif name == "hotspots":
        print(f"    Repos analyzed: {result.get('repos_analyzed', 0)}")
        print(f"    High-risk files: {result.get('high_risk_count', 0)}")
    elif name == "knowledge":
        print(f"    Bridge people: {result.get('bridge_people_count', 0)}")
        print(f"    Knowledge islands: {len(result.get('knowledge_islands', []))}")
        print(f"    Owner mismatches: {result.get('owner_mismatches', 0)}")
    elif name == "temporal":
        print(f"    Dormant repos: {result.get('dormant_repos', 0)}")
        print(f"    Burst events: {result.get('total_bursts', 0)}")
        print(f"    Cross-repo waves: {result.get('wave_events', 0)}")
    elif name == "integrate":
        print(f"    New findings integrated: {result.get('total_new', 0)}")

    print(f"    Time: {elapsed:.1f}s")


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write changes")
@click.option(
    "--only",
    type=click.Choice(RUN_ORDER),
    default=None,
    help="Run only one analyzer",
)
@click.option("--months", default=config.DEFAULT_HISTORY_MONTHS, help="Months of history to analyze")
@click.option("--window-hours", default=config.DEFAULT_COUPLING_WINDOW_HOURS, help="Co-change window in hours")
@click.option("--all-repos", is_flag=True, help="Analyze all discovered repos, not just audited ones")
@click.option("--anonymize", is_flag=True, help="Replace author names with hashed identifiers")
def main(
    dry_run: bool,
    only: str | None,
    months: int,
    window_hours: int,
    all_repos: bool,
    anonymize: bool,
) -> None:
    """Run all git-history analyses in dependency order."""
    order = [only] if only else RUN_ORDER

    print("=" * 60)
    print("MCP GIT HISTORY ANALYSIS ENGINE")
    print("=" * 60)

    if dry_run:
        print("  (dry run mode — no files will be written)")

    # Step 0: fetch all histories once (shared across analyzers)
    print(f"\nFetching git histories ({months} months)...")
    t0 = time.time()
    histories = git_log.fetch_all_histories(
        months=months,
        only_audited=not all_repos,
    )
    fetch_elapsed = time.time() - t0
    print(f"  Fetched {len(histories)} repos in {fetch_elapsed:.1f}s")

    if anonymize:
        print("  Anonymizing author data...")
        _anonymize_histories(histories)

    total_start = time.time()
    summary: dict[str, dict] = {}

    for name in order:
        label, mod = ANALYZERS[name]
        t0 = time.time()

        if name == "integrate":
            result = mod.run(dry_run=dry_run)
        elif name == "coupling":
            result = mod.run(
                dry_run=dry_run,
                months=months,
                window_hours=window_hours,
                histories=histories,
            )
        else:
            result = mod.run(
                dry_run=dry_run,
                months=months,
                histories=histories,
            )

        elapsed = time.time() - t0
        summary[name] = result
        _print_result(name, label, result, elapsed)

    total_elapsed = time.time() - total_start

    print(f"\n{'=' * 60}")
    print(f"HISTORY ANALYSIS COMPLETE ({total_elapsed:.1f}s total)")
    print(f"{'=' * 60}")

    if "coupling" in summary:
        r = summary["coupling"]
        print(f"  Coupling:     {r.get('total_pairs', 0)} pairs ({r.get('undocumented_couplings', 0)} undocumented)")
    if "hotspots" in summary:
        r = summary["hotspots"]
        print(f"  Hotspots:     {r.get('total_hotspots', 0)} total ({r.get('high_risk_count', 0)} high-risk)")
    if "knowledge" in summary:
        r = summary["knowledge"]
        print(f"  Knowledge:    {r.get('bridge_people_count', 0)} bridge people, "
              f"{r.get('low_bus_factor_repos', 0)} low-bus-factor repos")
    if "temporal" in summary:
        r = summary["temporal"]
        print(f"  Temporal:     {r.get('dormant_repos', 0)} dormant, {r.get('total_bursts', 0)} bursts")
    if "integrate" in summary:
        r = summary["integrate"]
        print(f"  Integration:  {r.get('total_new', 0)} new findings added to maps")


def _anonymize_histories(histories: dict[str, git_log.RepoHistory]) -> None:
    """Replace author names/emails with hashed identifiers in-place."""
    for history in histories.values():
        for commit in history.commits:
            key = git_log.normalise_author(commit.author_name, commit.author_email)
            anon = git_log.anonymise_author(key)
            commit.author_name = anon
            commit.author_email = f"{anon}@anon"


if __name__ == "__main__":
    main()
