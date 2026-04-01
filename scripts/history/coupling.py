#!/usr/bin/env python3
"""Co-change coupling analyzer.

Detects repos that change together within a time window, suggesting
hidden dependencies invisible in static analysis.
"""

from __future__ import annotations

import json
import sys
from datetime import timedelta
from itertools import combinations
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from history.git_log import (
    RepoHistory,
    fetch_all_histories,
    normalise_author,
)


# ── Analysis ─────────────────────────────────────────────────────────────────


def _repo_authors(history: RepoHistory) -> set[str]:
    return {
        normalise_author(c.author_name, c.author_email)
        for c in history.commits
    }


def _count_co_changes(
    hist_a: RepoHistory,
    hist_b: RepoHistory,
    window_hours: int,
) -> int:
    """Count commits in A that have at least one commit in B within the window."""
    if not hist_a.commits or not hist_b.commits:
        return 0

    window = timedelta(hours=window_hours)
    b_times = sorted(c.timestamp for c in hist_b.commits)

    co_changes = 0
    for commit_a in hist_a.commits:
        t = commit_a.timestamp
        # Binary search would be faster, but repos have ≤ thousands of commits
        for t_b in b_times:
            if abs(t - t_b) <= window:
                co_changes += 1
                break

    return co_changes


def _load_known_dependencies() -> set[tuple[str, str]]:
    """Load known dependency pairs from dependency-matrix.json."""
    dep_path = config.MAPS_DATA_DIR / "dependency-matrix.json"
    if not dep_path.is_file():
        return set()

    data = json.loads(dep_path.read_text())
    pairs: set[tuple[str, str]] = set()
    for edge in data.get("edges", []):
        a = edge.get("from", "")
        b = edge.get("to", "")
        if a and b:
            pairs.add((min(a, b), max(a, b)))
    return pairs


def compute_coupling(
    histories: dict[str, RepoHistory],
    window_hours: int = config.DEFAULT_COUPLING_WINDOW_HOURS,
) -> list[dict]:
    """Compute pairwise coupling scores for all repo pairs."""
    known_deps = _load_known_dependencies()
    pairs: list[dict] = []

    repo_names = sorted(histories.keys())
    for name_a, name_b in combinations(repo_names, 2):
        hist_a = histories[name_a]
        hist_b = histories[name_b]

        total_a = len(hist_a.commits)
        total_b = len(hist_b.commits)

        if total_a == 0 or total_b == 0:
            continue

        co_changes = _count_co_changes(hist_a, hist_b, window_hours)
        if co_changes == 0:
            continue

        # Normalise by the less-active repo to avoid false positives
        base_score = co_changes / min(total_a, total_b)

        # Author overlap weighting
        authors_a = _repo_authors(hist_a)
        authors_b = _repo_authors(hist_b)
        shared = authors_a & authors_b
        total_authors = len(authors_a | authors_b)
        author_weight = 1.0 + 0.5 * (len(shared) / total_authors) if total_authors > 0 else 1.0
        coupling_score = round(min(base_score * author_weight, 1.0), 2)

        pair_key = (min(name_a, name_b), max(name_a, name_b))
        is_known = pair_key in known_deps

        if is_known:
            finding = "Expected — known dependency"
        elif coupling_score >= 0.5:
            finding = "UNDOCUMENTED coupling — investigate"
        elif coupling_score >= 0.3:
            finding = "Possible undocumented coupling"
        else:
            finding = "Low coupling — likely coincidental"

        pairs.append({
            "repo_a": name_a,
            "repo_b": name_b,
            "coupling_score": coupling_score,
            "co_changes": co_changes,
            "total_changes_a": total_a,
            "total_changes_b": total_b,
            "shared_authors": sorted(shared),
            "known_dependency": is_known,
            "finding": finding,
        })

    pairs.sort(key=lambda p: p["coupling_score"], reverse=True)
    return pairs


# ── Output ───────────────────────────────────────────────────────────────────


def run(
    dry_run: bool = False,
    months: int = config.DEFAULT_HISTORY_MONTHS,
    window_hours: int = config.DEFAULT_COUPLING_WINDOW_HOURS,
    histories: dict[str, RepoHistory] | None = None,
) -> dict:
    """Run the co-change coupling analysis. Returns summary stats."""
    if histories is None:
        histories = fetch_all_histories(months=months)

    pairs = compute_coupling(histories, window_hours=window_hours)

    output = {
        "schema_version": "1.0",
        "window_hours": window_hours,
        "analysis_period_months": months,
        "pairs": pairs,
    }

    out_path = config.MAPS_DATA_DIR / "co-change-coupling.json"

    if not dry_run:
        out_path.write_text(json.dumps(output, indent=2) + "\n")

    undocumented = [p for p in pairs if not p["known_dependency"] and p["coupling_score"] >= 0.3]

    return {
        "total_pairs": len(pairs),
        "undocumented_couplings": len(undocumented),
        "top_score": pairs[0]["coupling_score"] if pairs else 0.0,
        "output": output,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write output files")
@click.option("--months", default=config.DEFAULT_HISTORY_MONTHS, help="Months of history to analyze")
@click.option("--window-hours", default=config.DEFAULT_COUPLING_WINDOW_HOURS, help="Co-change window in hours")
def main(dry_run: bool, months: int, window_hours: int) -> None:
    """Detect co-change coupling between repos."""
    result = run(dry_run=dry_run, months=months, window_hours=window_hours)

    print(f"\nCo-Change Coupling Analysis")
    print(f"{'=' * 40}")
    print(f"  Pairs analyzed: {result['total_pairs']}")
    print(f"  Undocumented couplings (score >= 0.3): {result['undocumented_couplings']}")
    print(f"  Top coupling score: {result['top_score']}")

    if result["output"]["pairs"]:
        print(f"\n  Top pairs:")
        for p in result["output"]["pairs"][:10]:
            marker = "*" if not p["known_dependency"] else " "
            print(f"   {marker} {p['repo_a']} <-> {p['repo_b']}: "
                  f"{p['coupling_score']} ({p['co_changes']} co-changes) "
                  f"[{p['finding']}]")

    if dry_run:
        print(f"\n  (dry run — no files written)")


if __name__ == "__main__":
    main()
