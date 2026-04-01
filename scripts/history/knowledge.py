#!/usr/bin/env python3
"""Knowledge distribution map.

Answers: who actually knows what? Where are the bus-factor risks?
Identifies bridge people, knowledge islands, and owner mismatches.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import click
import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from history.git_log import (
    RepoHistory,
    fetch_all_histories,
    normalise_author,
)


# ── Per-repo contributor analysis ────────────────────────────────────────────


def _rank_contributors(history: RepoHistory, now: datetime | None = None) -> list[dict]:
    """Rank contributors by weighted score: commit share * 0.7 + recency * 0.3."""
    if now is None:
        now = datetime.now(timezone.utc)

    author_stats: dict[str, dict] = defaultdict(lambda: {
        "commits": 0,
        "last_commit": None,
        "name": "",
    })

    for commit in history.commits:
        key = normalise_author(commit.author_name, commit.author_email)
        s = author_stats[key]
        s["commits"] += 1
        s["name"] = commit.author_name
        if s["last_commit"] is None or commit.timestamp > s["last_commit"]:
            s["last_commit"] = commit.timestamp

    if not author_stats:
        return []

    total_commits = sum(s["commits"] for s in author_stats.values())
    max_age_days = 180.0

    ranked = []
    for key, s in author_stats.items():
        commit_share = s["commits"] / total_commits if total_commits > 0 else 0

        if s["last_commit"]:
            days_ago = (now - s["last_commit"]).total_seconds() / 86400
            recency = max(0.0, 1.0 - days_ago / max_age_days)
        else:
            recency = 0.0

        score = round(0.7 * commit_share + 0.3 * recency, 3)
        ranked.append({
            "author": key,
            "display_name": s["name"],
            "commits": s["commits"],
            "last_commit": s["last_commit"].isoformat() if s["last_commit"] else None,
            "score": score,
        })

    ranked.sort(key=lambda r: -r["score"])
    return ranked


def _compute_bus_factor(ranked: list[dict]) -> int:
    """Minimum number of people covering >= 50% of commits."""
    if not ranked:
        return 0

    total = sum(r["commits"] for r in ranked)
    threshold = total * 0.5
    cumulative = 0

    for i, r in enumerate(ranked, 1):
        cumulative += r["commits"]
        if cumulative >= threshold:
            return i

    return len(ranked)


def _find_sole_experts(history: RepoHistory, min_changes: int = 5) -> list[dict]:
    """Find files with high change frequency touched by only one author."""
    file_authors: dict[str, set[str]] = defaultdict(set)
    file_frequency: dict[str, int] = defaultdict(int)

    for commit in history.commits:
        author = normalise_author(commit.author_name, commit.author_email)
        for fc in commit.files_changed:
            file_authors[fc.path].add(author)
            file_frequency[fc.path] += 1

    experts = []
    for path, authors in file_authors.items():
        if len(authors) == 1 and file_frequency[path] >= min_changes:
            experts.append({
                "path": path,
                "sole_author": next(iter(authors)),
                "change_frequency": file_frequency[path],
            })

    experts.sort(key=lambda e: -e["change_frequency"])
    return experts


# ── Cross-repo analysis ─────────────────────────────────────────────────────


def _find_bridge_people(
    histories: dict[str, RepoHistory],
    min_repos: int = 3,
) -> list[dict]:
    """Find contributors active in multiple repos."""
    author_repos: dict[str, set[str]] = defaultdict(set)
    author_names: dict[str, str] = {}

    for name, history in histories.items():
        for commit in history.commits:
            key = normalise_author(commit.author_name, commit.author_email)
            author_repos[key].add(name)
            author_names[key] = commit.author_name

    bridges = []
    for key, repos in author_repos.items():
        if len(repos) >= min_repos:
            bridges.append({
                "author": key,
                "display_name": author_names.get(key, key),
                "repos": sorted(repos),
                "repo_count": len(repos),
            })

    bridges.sort(key=lambda b: -b["repo_count"])
    return bridges


def _find_knowledge_islands(histories: dict[str, RepoHistory]) -> list[str]:
    """Find repos whose contributors don't overlap with any other repo."""
    repo_authors: dict[str, set[str]] = {}
    for name, history in histories.items():
        authors = set()
        for commit in history.commits:
            authors.add(normalise_author(commit.author_name, commit.author_email))
        repo_authors[name] = authors

    islands = []
    repo_names = sorted(repo_authors.keys())
    for name in repo_names:
        is_island = True
        for other in repo_names:
            if other == name:
                continue
            if repo_authors[name] & repo_authors[other]:
                is_island = False
                break
        if is_island and repo_authors[name]:
            islands.append(name)

    return islands


# ── Owner verification ───────────────────────────────────────────────────────


def _parse_inventory_owners() -> dict[str, str]:
    """Extract owner field per repo from INVENTORY.md."""
    if not config.INVENTORY_PATH.is_file():
        return {}

    text = config.INVENTORY_PATH.read_text()
    owners: dict[str, str] = {}

    for line in text.split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 6:
            continue
        repo = cells[1].strip().strip("_")
        if repo in ("Repo", "---", ""):
            continue
        owner = cells[4].strip()
        if owner and owner != "---":
            owners[repo] = owner

    return owners


def _verify_owners(
    histories: dict[str, RepoHistory],
    inventory_owners: dict[str, str],
) -> list[dict]:
    """Check if listed owners actually appear in commit history."""
    mismatches = []

    for repo_name, owner_str in inventory_owners.items():
        if repo_name not in histories:
            continue

        history = histories[repo_name]
        ranked = _rank_contributors(history)

        if not ranked:
            continue

        top_authors = {r["author"] for r in ranked[:5]}
        top_names = {r["display_name"].lower() for r in ranked[:5]}

        owner_lower = owner_str.lower().strip().strip("@")
        owner_parts = re.split(r"[,;/]|\band\b", owner_lower)
        owner_tokens = {p.strip().strip("@").strip() for p in owner_parts if p.strip()}

        found = False
        for token in owner_tokens:
            if any(token in a for a in top_authors):
                found = True
                break
            if any(token in n for n in top_names):
                found = True
                break

        if not found:
            mismatches.append({
                "repo": repo_name,
                "listed_owner": owner_str,
                "top_contributors": [r["display_name"] for r in ranked[:3]],
            })

    return mismatches


# ── Output ───────────────────────────────────────────────────────────────────


def run(
    dry_run: bool = False,
    months: int = config.DEFAULT_HISTORY_MONTHS,
    histories: dict[str, RepoHistory] | None = None,
) -> dict:
    """Run knowledge distribution analysis. Returns summary stats."""
    if histories is None:
        histories = fetch_all_histories(months=months)

    repos_output: dict[str, dict] = {}
    total_sole_experts = 0
    low_bus_factor_repos = 0

    for name, history in sorted(histories.items()):
        ranked = _rank_contributors(history)
        bus_factor = _compute_bus_factor(ranked)
        sole_experts = _find_sole_experts(history)

        repos_output[name] = {
            "contributors": ranked[:10],
            "bus_factor": bus_factor,
            "sole_experts": sole_experts[:10],
        }

        total_sole_experts += len(sole_experts)
        if bus_factor <= 1:
            low_bus_factor_repos += 1

    bridge_people = _find_bridge_people(histories)
    knowledge_islands = _find_knowledge_islands(histories)
    inventory_owners = _parse_inventory_owners()
    owner_mismatches = _verify_owners(histories, inventory_owners)

    output = {
        "schema_version": "1.0",
        "analysis_period_months": months,
        "repos": repos_output,
        "bridge_people": bridge_people,
        "knowledge_islands": knowledge_islands,
        "owner_mismatches": owner_mismatches,
    }

    out_path = config.MAPS_DATA_DIR / "knowledge-distribution.json"
    if not dry_run:
        out_path.write_text(json.dumps(output, indent=2) + "\n")

    return {
        "repos_analyzed": len(repos_output),
        "bridge_people_count": len(bridge_people),
        "knowledge_islands": knowledge_islands,
        "owner_mismatches": len(owner_mismatches),
        "low_bus_factor_repos": low_bus_factor_repos,
        "total_sole_experts": total_sole_experts,
        "output": output,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write output files")
@click.option("--months", default=config.DEFAULT_HISTORY_MONTHS, help="Months of history to analyze")
def main(dry_run: bool, months: int) -> None:
    """Analyze knowledge distribution across repos."""
    result = run(dry_run=dry_run, months=months)

    print(f"\nKnowledge Distribution")
    print(f"{'=' * 40}")
    print(f"  Repos analyzed: {result['repos_analyzed']}")
    print(f"  Low bus-factor repos (<=1): {result['low_bus_factor_repos']}")
    print(f"  Sole expert files: {result['total_sole_experts']}")
    print(f"  Bridge people (3+ repos): {result['bridge_people_count']}")
    print(f"  Knowledge islands: {len(result['knowledge_islands'])}")
    print(f"  Owner mismatches: {result['owner_mismatches']}")

    if result["output"]["bridge_people"]:
        print(f"\n  Bridge people:")
        for bp in result["output"]["bridge_people"][:5]:
            print(f"    {bp['display_name']}: {', '.join(bp['repos'])}")

    if result["knowledge_islands"]:
        print(f"\n  Knowledge islands: {', '.join(result['knowledge_islands'])}")

    if result["output"]["owner_mismatches"]:
        print(f"\n  Owner mismatches:")
        for om in result["output"]["owner_mismatches"]:
            print(f"    {om['repo']}: listed={om['listed_owner']}, "
                  f"top contributors={', '.join(om['top_contributors'])}")

    if dry_run:
        print(f"\n  (dry run — no files written)")


if __name__ == "__main__":
    main()
