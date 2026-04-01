#!/usr/bin/env python3
"""Temporal pattern detector.

Detects time-based patterns that reveal operational behavior: deploy cadence,
dormancy, activity bursts, day-of-week patterns, and cross-repo waves.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from history.git_log import (
    RepoHistory,
    fetch_all_histories,
)


# ── Weekly bucketing ─────────────────────────────────────────────────────────


def _week_key(dt: datetime) -> str:
    """ISO year-week string like '2026-W13'."""
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _bucket_by_week(history: RepoHistory) -> dict[str, int]:
    """Count commits per ISO week."""
    weeks: dict[str, int] = defaultdict(int)
    for commit in history.commits:
        weeks[_week_key(commit.timestamp)] += 1
    return dict(weeks)


def _all_weeks_in_range(start: datetime, end: datetime) -> list[str]:
    """Generate all ISO week keys between two dates."""
    weeks = []
    current = start
    seen: set[str] = set()
    while current <= end:
        wk = _week_key(current)
        if wk not in seen:
            weeks.append(wk)
            seen.add(wk)
        current += timedelta(days=7)
    return weeks


# ── Deploy cadence ───────────────────────────────────────────────────────────


def _compute_cadence(history: RepoHistory) -> dict:
    """Compute commits-per-week stats."""
    weeks = _bucket_by_week(history)
    if not weeks:
        return {"commits_per_week_avg": 0.0, "commits_per_week_median": 0.0, "active_weeks": 0}

    counts = list(weeks.values())
    return {
        "commits_per_week_avg": round(statistics.mean(counts), 1),
        "commits_per_week_median": round(statistics.median(counts), 1),
        "active_weeks": len(weeks),
        "total_commits": sum(counts),
    }


# ── Dormancy detection ──────────────────────────────────────────────────────


def _check_dormancy(
    history: RepoHistory,
    dormancy_months: int = 3,
    now: datetime | None = None,
) -> dict | None:
    """Return dormancy info if repo has no commits in the last N months."""
    if now is None:
        now = datetime.now(timezone.utc)

    if not history.commits:
        return {
            "repo": history.repo_name,
            "last_activity": None,
            "dormant_days": None,
            "status": "no commits in analysis window",
        }

    last_commit = max(c.timestamp for c in history.commits)
    cutoff = now - timedelta(days=dormancy_months * 30)

    if last_commit < cutoff:
        dormant_days = (now - last_commit).days
        return {
            "repo": history.repo_name,
            "last_activity": last_commit.isoformat(),
            "dormant_days": dormant_days,
            "status": f"dormant ({dormant_days} days since last commit)",
        }

    return None


# ── Burst detection ──────────────────────────────────────────────────────────


def _detect_bursts(history: RepoHistory) -> list[dict]:
    """Find weeks where activity exceeds mean + 2 * stddev."""
    weeks = _bucket_by_week(history)
    if len(weeks) < 4:
        return []

    counts = list(weeks.values())
    mean = statistics.mean(counts)
    stdev = statistics.stdev(counts) if len(counts) > 1 else 0.0
    threshold = mean + 2 * stdev

    if stdev == 0:
        return []

    bursts = []
    for week, count in sorted(weeks.items()):
        if count > threshold:
            bursts.append({
                "week": week,
                "commits": count,
                "threshold": round(threshold, 1),
                "z_score": round((count - mean) / stdev, 1) if stdev > 0 else 0,
            })

    return bursts


# ── Day-of-week patterns ────────────────────────────────────────────────────


def _day_of_week_distribution(history: RepoHistory) -> dict[str, float]:
    """Compute commit percentage by day of week."""
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    counts: dict[int, int] = defaultdict(int)

    for commit in history.commits:
        counts[commit.timestamp.weekday()] += 1

    total = sum(counts.values())
    if total == 0:
        return {name: 0.0 for name in day_names}

    return {
        name: round(counts.get(i, 0) / total * 100, 1)
        for i, name in enumerate(day_names)
    }


# ── Cross-repo waves ────────────────────────────────────────────────────────


def _detect_waves(
    histories: dict[str, RepoHistory],
    wave_window_weeks: int = 1,
) -> list[dict]:
    """When repo A bursts, check if other repos burst within N weeks."""
    repo_bursts: dict[str, set[str]] = {}
    for name, history in histories.items():
        bursts = _detect_bursts(history)
        repo_bursts[name] = {b["week"] for b in bursts}

    waves = []
    repo_names = sorted(histories.keys())

    for source in repo_names:
        if not repo_bursts[source]:
            continue

        for burst_week in sorted(repo_bursts[source]):
            followers = []
            for other in repo_names:
                if other == source:
                    continue
                # Check if the other repo also bursts within wave_window_weeks
                for other_week in repo_bursts[other]:
                    if _weeks_apart(burst_week, other_week) <= wave_window_weeks:
                        followers.append(other)
                        break

            if followers:
                waves.append({
                    "source_repo": source,
                    "week": burst_week,
                    "follower_repos": sorted(followers),
                })

    # Deduplicate symmetric waves (A triggers B == B triggers A)
    seen: set[str] = set()
    deduped: list[dict] = []
    for w in waves:
        key = f"{w['week']}:{','.join(sorted([w['source_repo']] + w['follower_repos']))}"
        if key not in seen:
            seen.add(key)
            deduped.append(w)

    return deduped


def _weeks_apart(week_a: str, week_b: str) -> int:
    """Approximate distance in weeks between two ISO week strings."""
    try:
        ya, wa = week_a.split("-W")
        yb, wb = week_b.split("-W")
        abs_a = int(ya) * 52 + int(wa)
        abs_b = int(yb) * 52 + int(wb)
        return abs(abs_a - abs_b)
    except (ValueError, IndexError):
        return 999


# ── Output ───────────────────────────────────────────────────────────────────


def run(
    dry_run: bool = False,
    months: int = config.DEFAULT_HISTORY_MONTHS,
    dormancy_months: int = 3,
    histories: dict[str, RepoHistory] | None = None,
) -> dict:
    """Run temporal pattern analysis. Returns summary stats."""
    if histories is None:
        histories = fetch_all_histories(months=months)

    repos_output: dict[str, dict] = {}
    dormant_repos: list[dict] = []

    for name, history in sorted(histories.items()):
        cadence = _compute_cadence(history)
        bursts = _detect_bursts(history)
        dow = _day_of_week_distribution(history)
        dormancy = _check_dormancy(history, dormancy_months=dormancy_months)

        repos_output[name] = {
            "cadence": cadence,
            "bursts": bursts,
            "day_of_week": dow,
        }

        if dormancy:
            dormant_repos.append(dormancy)

    waves = _detect_waves(histories)

    weekend_deployers = []
    for name, data in repos_output.items():
        dow = data["day_of_week"]
        weekend_pct = dow.get("Saturday", 0) + dow.get("Sunday", 0)
        if weekend_pct > 15:
            weekend_deployers.append({
                "repo": name,
                "weekend_pct": round(weekend_pct, 1),
            })

    output = {
        "schema_version": "1.0",
        "analysis_period_months": months,
        "dormancy_threshold_months": dormancy_months,
        "repos": repos_output,
        "dormant_repos": dormant_repos,
        "cross_repo_waves": waves,
        "weekend_deployers": weekend_deployers,
    }

    out_path = config.MAPS_DATA_DIR / "temporal-patterns.json"
    if not dry_run:
        out_path.write_text(json.dumps(output, indent=2) + "\n")

    total_bursts = sum(len(d["bursts"]) for d in repos_output.values())

    return {
        "repos_analyzed": len(repos_output),
        "dormant_repos": len(dormant_repos),
        "total_bursts": total_bursts,
        "wave_events": len(waves),
        "weekend_deployers": len(weekend_deployers),
        "output": output,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write output files")
@click.option("--months", default=config.DEFAULT_HISTORY_MONTHS, help="Months of history to analyze")
@click.option("--dormancy-months", default=3, help="Months of inactivity for dormancy flag")
def main(dry_run: bool, months: int, dormancy_months: int) -> None:
    """Detect temporal patterns in repo activity."""
    result = run(dry_run=dry_run, months=months, dormancy_months=dormancy_months)

    print(f"\nTemporal Patterns")
    print(f"{'=' * 40}")
    print(f"  Repos analyzed: {result['repos_analyzed']}")
    print(f"  Dormant repos: {result['dormant_repos']}")
    print(f"  Burst events: {result['total_bursts']}")
    print(f"  Cross-repo waves: {result['wave_events']}")
    print(f"  Weekend deployers: {result['weekend_deployers']}")

    if result["output"]["dormant_repos"]:
        print(f"\n  Dormant repos:")
        for d in result["output"]["dormant_repos"]:
            print(f"    {d['repo']}: {d['status']}")

    if result["output"]["cross_repo_waves"]:
        print(f"\n  Cross-repo waves:")
        for w in result["output"]["cross_repo_waves"][:5]:
            print(f"    {w['week']}: {w['source_repo']} -> {', '.join(w['follower_repos'])}")

    if dry_run:
        print(f"\n  (dry run — no files written)")


if __name__ == "__main__":
    main()
