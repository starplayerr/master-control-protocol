#!/usr/bin/env python3
"""Dashboard data generator.

Aggregates all feedback metrics into a single JSON file suitable for
charting with recharts, Chart.js, or rendering as markdown tables:

- Total audits run, by month
- Prompt effectiveness trends
- Map quality trends
- Contradiction open/resolved trend
- Stale assumption discovery rate
- Simplification completion rate
- Overall "platform understanding score" (composite metric)

Output: feedback/dashboard.json
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from lib.cache import get_state
from feedback.capture import load_capture_log
from feedback.prompt_score import score_prompts
from feedback.map_quality import score_maps


def _audit_timeline(audit_state: dict) -> list[dict]:
    """Build monthly audit counts from audit state."""
    monthly: dict[str, int] = defaultdict(int)

    for repo_name, state in audit_state.get("repos", {}).items():
        date_str = state.get("last_audit_date", "")
        if date_str:
            month = date_str[:7]  # YYYY-MM
            monthly[month] += 1

    return [
        {"month": m, "audits": c}
        for m, c in sorted(monthly.items())
    ]


def _capture_timeline(capture_log: list[dict]) -> list[dict]:
    """Build monthly capture counts by type."""
    monthly: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for entry in capture_log:
        ts = entry.get("timestamp", "")
        month = ts[:7] if ts else "unknown"
        for cap in entry.get("captures", []):
            cap_type = cap.get("type", "unknown")
            monthly[month][cap_type] += 1
            monthly[month]["total"] += 1

    return [
        {"month": m, **counts}
        for m, counts in sorted(monthly.items())
    ]


def _contradiction_summary() -> dict:
    """Open vs resolved contradictions."""
    path = config.MAPS_DATA_DIR / "contradictions-and-ambiguities.json"
    if not path.is_file():
        return {"open": 0, "resolved": 0, "total": 0}

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"open": 0, "resolved": 0, "total": 0}

    items = data.get("items", [])
    total = len(items)
    resolved = sum(
        1 for i in items
        if i.get("status", "").lower() in ("resolved", "dismissed", "closed")
    )
    return {"open": total - resolved, "resolved": resolved, "total": total}


def _stale_assumption_summary() -> dict:
    """Stale assumptions status."""
    path = config.MAPS_DATA_DIR / "stale-assumptions.json"
    if not path.is_file():
        return {"open": 0, "resolved": 0, "total": 0}

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"open": 0, "resolved": 0, "total": 0}

    items = data.get("items", [])
    total = len(items)
    resolved = sum(
        1 for i in items
        if i.get("status", "").lower() in ("resolved", "dismissed", "closed")
    )
    return {"open": total - resolved, "resolved": resolved, "total": total}


def _simplification_summary() -> dict:
    """Simplification candidates and completion."""
    path = config.MAPS_DATA_DIR / "candidate-simplifications.json"
    if not path.is_file():
        return {"total": 0, "acted_on": 0, "completion_rate": 0.0}

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"total": 0, "acted_on": 0, "completion_rate": 0.0}

    candidates = data.get("candidates", [])
    total = len(candidates)
    acted = sum(
        1 for c in candidates
        if c.get("status", "").lower() in ("completed", "in-progress", "done")
    )
    return {
        "total": total,
        "acted_on": acted,
        "completion_rate": round(acted / max(total, 1), 3),
    }


def _platform_understanding_score(
    audit_state: dict,
    prompt_scores: dict,
    map_scores: dict,
    contradictions: dict,
) -> float:
    """Composite metric: how well does MCP understand the platform?

    Components (weighted):
    - Audit coverage (25%): % of discovered repos audited
    - Prompt effectiveness (20%): avg completeness across prompts
    - Map quality (20%): avg quality score across maps
    - Contradiction resolution (15%): % resolved
    - Freshness (10%): % of audits current (not stale)
    - Feedback maturity (10%): has capture data flowing
    """
    # Audit coverage
    total_repos = len(audit_state.get("repos", {}))
    audited = sum(1 for r in audit_state.get("repos", {}).values() if r.get("status") == "current")
    coverage = audited / max(total_repos, 1)

    # Prompt effectiveness
    if prompt_scores:
        avg_completeness = sum(
            s.get("avg_completeness", 0) for s in prompt_scores.values()
        ) / len(prompt_scores)
    else:
        avg_completeness = 0.0

    # Map quality
    if map_scores:
        avg_map_quality = sum(
            s.get("quality_score", 0) for s in map_scores.values()
        ) / len(map_scores)
    else:
        avg_map_quality = 0.0

    # Contradiction resolution
    total_contradictions = contradictions.get("total", 0)
    resolved = contradictions.get("resolved", 0)
    resolution = resolved / max(total_contradictions, 1)

    # Freshness: all current audits
    fresh = sum(1 for r in audit_state.get("repos", {}).values() if r.get("status") == "current")
    freshness = fresh / max(total_repos, 1)

    # Feedback maturity: do we have capture data?
    capture_log = load_capture_log()
    has_feedback = min(len(capture_log) / 10, 1.0)  # saturates at 10 entries

    score = (
        coverage * 0.25
        + avg_completeness * 0.20
        + avg_map_quality * 0.20
        + resolution * 0.15
        + freshness * 0.10
        + has_feedback * 0.10
    )

    return round(score, 3)


def generate_dashboard(dry_run: bool = False) -> dict:
    """Generate the full dashboard data object."""
    audit_state = get_state()
    prompt_scores = score_prompts(dry_run=True)
    map_scores = score_maps(dry_run=True)
    capture_log = load_capture_log()
    contradictions = _contradiction_summary()
    stale = _stale_assumption_summary()
    simplifications = _simplification_summary()

    pus = _platform_understanding_score(
        audit_state, prompt_scores, map_scores, contradictions,
    )

    dashboard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform_understanding_score": pus,
        "audit_summary": {
            "total_repos": len(audit_state.get("repos", {})),
            "current": sum(1 for r in audit_state.get("repos", {}).values() if r.get("status") == "current"),
            "stale": sum(1 for r in audit_state.get("repos", {}).values() if r.get("status") == "stale"),
        },
        "audit_timeline": _audit_timeline(audit_state),
        "capture_timeline": _capture_timeline(capture_log),
        "prompt_effectiveness": prompt_scores,
        "map_quality": {
            k: {
                "grade": v.get("overall_quality", "?"),
                "score": v.get("quality_score", 0),
                "coverage": v.get("coverage", 0),
                "freshness": v.get("freshness", "unknown"),
            }
            for k, v in map_scores.items()
        },
        "contradictions": contradictions,
        "stale_assumptions": stale,
        "simplifications": simplifications,
        "feedback_loop_health": {
            "total_captures": len(capture_log),
            "total_findings": sum(len(e.get("captures", [])) for e in capture_log),
            "prompt_gaps": sum(
                1 for e in capture_log
                for c in e.get("captures", [])
                if c.get("type") == "prompt-gap"
            ),
            "corrections": sum(
                1 for e in capture_log
                for c in e.get("captures", [])
                if c.get("type") == "correction"
            ),
            "cross_repo_insights": sum(
                1 for e in capture_log
                for c in e.get("captures", [])
                if c.get("type") == "cross-repo-insight"
            ),
        },
    }

    if not dry_run:
        config.FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
        config.DASHBOARD_PATH.write_text(
            json.dumps(dashboard, indent=2, sort_keys=True) + "\n"
        )

    return dashboard


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write dashboard file")
def main(dry_run: bool) -> None:
    """Generate dashboard data from all feedback sources."""
    dashboard = generate_dashboard(dry_run=dry_run)

    pus = dashboard["platform_understanding_score"]
    audit = dashboard["audit_summary"]
    fb = dashboard["feedback_loop_health"]
    cont = dashboard["contradictions"]

    click.echo(f"\n{'=' * 60}")
    click.echo("MCP FEEDBACK DASHBOARD")
    click.echo(f"{'=' * 60}")
    click.echo(f"\n  Platform Understanding Score: {pus:.1%}")
    click.echo(f"\n  Audits: {audit['current']} current, {audit['stale']} stale, {audit['total_repos']} total")
    click.echo(f"  Contradictions: {cont['open']} open, {cont['resolved']} resolved")
    click.echo(f"  Feedback: {fb['total_captures']} captures, {fb['prompt_gaps']} gaps, {fb['corrections']} corrections")

    click.echo(f"\n  Map Quality:")
    for map_file, mq in sorted(dashboard["map_quality"].items()):
        click.echo(f"    [{mq['grade']}] {map_file}")

    if not dry_run:
        click.echo(f"\n  Dashboard written to: {config.DASHBOARD_PATH}")


if __name__ == "__main__":
    main()
