#!/usr/bin/env python3
"""Map quality scoring.

Scores the overall quality and completeness of each synthesis map:
- Coverage: % of inventoried repos represented in the map
- Freshness: how old are entries relative to source audits
- Resolution rate: for contradictions/stale-assumptions, % resolved vs open
- Verification rate: % of entries that have been human-verified
- Actionability: for simplifications, how many have been acted on

Output: feedback/map-quality.json + appends to feedback/quality-history.jsonl
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click
import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from feedback.capture import load_capture_log

# Maps and their corresponding JSON data files
MAP_REGISTRY: dict[str, dict] = {
    "maps/contradictions-and-ambiguities.md": {
        "data": "maps/data/contradictions-and-ambiguities.json",
        "type": "issue-tracker",
        "items_key": "items",
    },
    "maps/stale-assumptions.md": {
        "data": "maps/data/stale-assumptions.json",
        "type": "issue-tracker",
        "items_key": "items",
    },
    "maps/candidate-simplifications.md": {
        "data": "maps/data/candidate-simplifications.json",
        "type": "actionable",
        "items_key": "candidates",
    },
    "maps/missing-docs.md": {
        "data": "maps/data/missing-docs.json",
        "type": "issue-tracker",
        "items_key": "items",
    },
    "maps/dependency-matrix.md": {
        "data": "maps/data/dependency-matrix.json",
        "type": "reference",
        "items_key": "edges",
    },
    "maps/deployment-flow.md": {
        "data": "maps/data/deployment-flow.json",
        "type": "reference",
        "items_key": "flows",
    },
    "maps/source-of-truth.md": {
        "data": "maps/data/source-of-truth.json",
        "type": "reference",
        "items_key": None,
    },
}

GRADE_THRESHOLDS = [
    (0.90, "A"),
    (0.80, "B"),
    (0.65, "C"),
    (0.50, "D"),
    (0.0, "F"),
]


def _letter_grade(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def _get_inventoried_repos() -> set[str]:
    """Parse INVENTORY.md for all repo names."""
    repos: set[str] = set()
    if not config.INVENTORY_PATH.is_file():
        return repos

    in_table = False
    for line in config.INVENTORY_PATH.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("| Repo") and "Surface" in stripped:
            in_table = True
            continue
        if in_table and stripped.startswith("|---"):
            continue
        if in_table and stripped.startswith("|"):
            cells = [c.strip().strip("_") for c in stripped.split("|")[1:-1]]
            if cells and cells[0]:
                repos.add(cells[0])
        elif in_table and not stripped.startswith("|"):
            break

    return repos


def _repos_in_data(data: dict, items_key: str | None) -> set[str]:
    """Extract all repo names referenced in a map's JSON data."""
    repos: set[str] = set()
    if items_key is None:
        # Flat structure — scan all values for repo-like strings
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            for r in item.get("repos", []):
                                repos.add(r)
        return repos

    items = data.get(items_key, [])
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                for r in item.get("repos", []):
                    repos.add(r)
                if "source" in item and isinstance(item["source"], str):
                    repo = Path(item["source"]).stem
                    if repo:
                        repos.add(repo)
                for src in item.get("sources", []):
                    if isinstance(src, str) and src.startswith("audits/"):
                        repos.add(Path(src).stem)

    return repos


def _freshness_from_frontmatter(map_path: Path) -> str:
    """Read freshness from map frontmatter."""
    if not map_path.is_file():
        return "missing"
    try:
        post = frontmatter.load(str(map_path))
        return str(post.metadata.get("freshness", "unknown"))
    except Exception:
        return "unknown"


def _resolution_rate(data: dict, items_key: str | None) -> tuple[int, int, float]:
    """For issue-tracker maps: count open vs resolved items."""
    if items_key is None:
        return 0, 0, 0.0

    items = data.get(items_key, [])
    if not isinstance(items, list):
        return 0, 0, 0.0

    total = len(items)
    resolved = sum(
        1 for item in items
        if isinstance(item, dict) and item.get("status", "").lower() in ("resolved", "dismissed", "closed")
    )

    rate = resolved / total if total > 0 else 0.0
    return total - resolved, resolved, rate


def _verification_rate(capture_log: list[dict], map_path_str: str) -> float:
    """Estimate human verification rate from capture log corrections."""
    total_relevant = 0
    verified = 0

    for entry in capture_log:
        for cap in entry.get("captures", []):
            if cap.get("type") == "correction":
                total_relevant += 1
                if cap.get("corrected_by") == "human":
                    verified += 1

    return verified / max(total_relevant, 1) if total_relevant > 0 else 0.0


def score_maps(dry_run: bool = False) -> dict:
    """Score all maps. Returns the scores dict."""
    inventoried_repos = _get_inventoried_repos()
    capture_log = load_capture_log()

    scores: dict[str, dict] = {}

    for map_file, meta in MAP_REGISTRY.items():
        map_path = config.MCP_ROOT / map_file
        data_path = config.MCP_ROOT / meta["data"]

        data: dict = {}
        if data_path.is_file():
            try:
                data = json.loads(data_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        # Coverage
        map_repos = _repos_in_data(data, meta["items_key"])
        coverage = len(map_repos & inventoried_repos) / max(len(inventoried_repos), 1)

        # Freshness
        freshness = _freshness_from_frontmatter(map_path)

        # Resolution rate (only meaningful for issue-tracker maps)
        open_items, resolved_items, resolution_rate = _resolution_rate(data, meta["items_key"])

        # Verification rate
        verification_rate = _verification_rate(capture_log, map_file)

        # Composite quality score
        freshness_score = 1.0 if freshness == "current" else (0.5 if freshness == "stale" else 0.0)
        quality_score = (
            coverage * 0.30
            + freshness_score * 0.25
            + resolution_rate * 0.20
            + verification_rate * 0.15
            + (0.10 if data else 0.0)  # has data at all
        )

        scores[map_file] = {
            "coverage": round(coverage, 3),
            "freshness": freshness,
            "open_items": open_items,
            "resolved_items": resolved_items,
            "resolution_rate": round(resolution_rate, 3),
            "verification_rate": round(verification_rate, 3),
            "quality_score": round(quality_score, 3),
            "overall_quality": _letter_grade(quality_score),
            "repos_covered": sorted(map_repos & inventoried_repos),
            "repos_missing": sorted(inventoried_repos - map_repos),
            "last_scored": datetime.now(timezone.utc).isoformat(),
        }

    # Find lowest-quality map
    if scores:
        worst = min(scores.items(), key=lambda x: x[1]["quality_score"])
        for s in scores.values():
            s["priority_improvement"] = False
        scores[worst[0]]["priority_improvement"] = True

    if not dry_run:
        config.FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
        config.MAP_QUALITY_PATH.write_text(
            json.dumps(scores, indent=2, sort_keys=True) + "\n"
        )

        # Append to history
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scores": {k: {"quality": v["overall_quality"], "score": v["quality_score"]}
                       for k, v in scores.items()},
        }
        with open(config.QUALITY_HISTORY_PATH, "a") as f:
            f.write(json.dumps(history_entry, sort_keys=True) + "\n")

    return scores


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write quality files")
def main(dry_run: bool) -> None:
    """Score map quality across all synthesis maps."""
    scores = score_maps(dry_run=dry_run)

    click.echo(f"\n{'=' * 60}")
    click.echo("MAP QUALITY SCORES")
    click.echo(f"{'=' * 60}")

    for map_file, s in sorted(scores.items(), key=lambda x: x[1]["quality_score"]):
        grade = s["overall_quality"]
        prio = " *** PRIORITY ***" if s.get("priority_improvement") else ""
        click.echo(f"\n  [{grade}] {map_file}{prio}")
        click.echo(f"    Coverage:        {s['coverage']:.0%}")
        click.echo(f"    Freshness:       {s['freshness']}")
        click.echo(f"    Open/Resolved:   {s['open_items']}/{s['resolved_items']}")
        click.echo(f"    Resolution rate: {s['resolution_rate']:.0%}")
        click.echo(f"    Verification:    {s['verification_rate']:.0%}")
        click.echo(f"    Quality score:   {s['quality_score']:.3f}")

    if dry_run:
        click.echo("\n  (dry run — no files written)")


if __name__ == "__main__":
    main()
