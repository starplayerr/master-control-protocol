#!/usr/bin/env python3
"""Change hotspot detector.

Identifies files and directories that change most frequently and carry
the most risk, combining frequency, churn, and knowledge concentration.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from history.git_log import (
    RepoHistory,
    fetch_all_histories,
    normalise_author,
)


# ── Per-file aggregation ────────────────────────────────────────────────────


def _aggregate_file_stats(history: RepoHistory) -> dict[str, dict]:
    """Aggregate per-file stats from commit history.

    Returns {path: {frequency, authors, total_added, total_deleted, co_files}}.
    """
    stats: dict[str, dict] = defaultdict(lambda: {
        "frequency": 0,
        "authors": set(),
        "total_added": 0,
        "total_deleted": 0,
        "co_files": defaultdict(int),
    })

    for commit in history.commits:
        paths_in_commit = [fc.path for fc in commit.files_changed]
        author = normalise_author(commit.author_name, commit.author_email)

        for fc in commit.files_changed:
            s = stats[fc.path]
            s["frequency"] += 1
            s["authors"].add(author)
            s["total_added"] += fc.added
            s["total_deleted"] += fc.deleted

            for other_path in paths_in_commit:
                if other_path != fc.path:
                    s["co_files"][other_path] += 1

    return dict(stats)


def _classify_churn(total_churn: int, frequency: int) -> str:
    """Classify churn rate as low/medium/high."""
    if frequency == 0:
        return "low"
    avg_churn = total_churn / frequency
    if avg_churn > 100:
        return "high"
    if avg_churn > 30:
        return "medium"
    return "low"


def _score_risk(frequency: int, author_count: int, churn: str) -> tuple[str, str]:
    """Return (risk_level, reason) based on combined signals."""
    reasons = []

    if frequency >= 20 and author_count <= 2:
        reasons.append("High churn, low author count — knowledge silo")
    elif frequency >= 20:
        reasons.append("High change frequency")

    if author_count == 1:
        reasons.append("Single author — bus factor risk")
    elif author_count <= 2 and frequency >= 10:
        reasons.append(f"Only {author_count} authors for a frequently-changed file")

    if churn == "high":
        reasons.append("High code churn (instability)")

    if not reasons:
        reason = "Normal activity"
        if frequency >= 10:
            risk = "medium"
        else:
            risk = "low"
    else:
        reason = "; ".join(reasons)
        high_signals = sum([
            frequency >= 20,
            author_count <= 2,
            churn == "high",
        ])
        risk = "high" if high_signals >= 2 else "medium"

    return risk, reason


TOP_N = 10


def compute_hotspots(history: RepoHistory) -> list[dict]:
    """Compute the top hotspots for a single repo."""
    file_stats = _aggregate_file_stats(history)

    hotspots = []
    for path, s in file_stats.items():
        frequency = s["frequency"]
        author_count = len(s["authors"])
        total_churn = s["total_added"] + s["total_deleted"]
        churn_rate = _classify_churn(total_churn, frequency)
        coupling_fan_out = len(s["co_files"])
        risk, reason = _score_risk(frequency, author_count, churn_rate)

        hotspots.append({
            "path": path,
            "change_frequency": frequency,
            "authors": author_count,
            "churn_rate": churn_rate,
            "coupling_fan_out": coupling_fan_out,
            "risk": risk,
            "reason": reason,
        })

    # Sort by composite: high risk first, then by frequency
    risk_order = {"high": 0, "medium": 1, "low": 2}
    hotspots.sort(key=lambda h: (risk_order.get(h["risk"], 3), -h["change_frequency"]))

    return hotspots[:TOP_N]


# ── Directory-level rollup ──────────────────────────────────────────────────


def _rollup_directories(history: RepoHistory) -> list[dict]:
    """Aggregate file-level stats to the top-level directory."""
    dir_stats: dict[str, dict] = defaultdict(lambda: {
        "frequency": 0,
        "authors": set(),
        "total_churn": 0,
        "file_count": 0,
    })

    for commit in history.commits:
        dirs_seen: set[str] = set()
        author = normalise_author(commit.author_name, commit.author_email)

        for fc in commit.files_changed:
            top_dir = fc.path.split("/")[0] if "/" in fc.path else "(root)"
            ds = dir_stats[top_dir]
            ds["authors"].add(author)
            ds["total_churn"] += fc.added + fc.deleted

            if top_dir not in dirs_seen:
                ds["frequency"] += 1
                dirs_seen.add(top_dir)

    results = []
    for dir_name, ds in dir_stats.items():
        results.append({
            "directory": dir_name,
            "change_frequency": ds["frequency"],
            "authors": len(ds["authors"]),
            "total_churn": ds["total_churn"],
        })

    results.sort(key=lambda d: -d["change_frequency"])
    return results[:TOP_N]


# ── Output ───────────────────────────────────────────────────────────────────


def run(
    dry_run: bool = False,
    months: int = config.DEFAULT_HISTORY_MONTHS,
    histories: dict[str, RepoHistory] | None = None,
) -> dict:
    """Run hotspot detection across all repos. Returns summary stats."""
    if histories is None:
        histories = fetch_all_histories(months=months)

    repos_output: dict[str, dict] = {}
    total_hotspots = 0
    high_risk_count = 0

    for name, history in sorted(histories.items()):
        hotspots = compute_hotspots(history)
        directories = _rollup_directories(history)

        repos_output[name] = {
            "hotspots": hotspots,
            "directories": directories,
        }
        total_hotspots += len(hotspots)
        high_risk_count += sum(1 for h in hotspots if h["risk"] == "high")

    output = {
        "schema_version": "1.0",
        "analysis_period_months": months,
        "repos": repos_output,
    }

    out_path = config.MAPS_DATA_DIR / "hotspots.json"
    if not dry_run:
        out_path.write_text(json.dumps(output, indent=2) + "\n")

    return {
        "total_hotspots": total_hotspots,
        "high_risk_count": high_risk_count,
        "repos_analyzed": len(repos_output),
        "output": output,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write output files")
@click.option("--months", default=config.DEFAULT_HISTORY_MONTHS, help="Months of history to analyze")
def main(dry_run: bool, months: int) -> None:
    """Detect change hotspots in repos."""
    result = run(dry_run=dry_run, months=months)

    print(f"\nHotspot Detector")
    print(f"{'=' * 40}")
    print(f"  Repos analyzed: {result['repos_analyzed']}")
    print(f"  Total hotspots: {result['total_hotspots']}")
    print(f"  High-risk files: {result['high_risk_count']}")

    for repo_name, data in result["output"]["repos"].items():
        high = [h for h in data["hotspots"] if h["risk"] == "high"]
        if high:
            print(f"\n  {repo_name}:")
            for h in high:
                print(f"    ! {h['path']} — {h['reason']}")

    if dry_run:
        print(f"\n  (dry run — no files written)")


if __name__ == "__main__":
    main()
