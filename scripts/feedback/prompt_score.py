#!/usr/bin/env python3
"""Prompt effectiveness tracker.

Measures how well each prompt variant performs over time:
- Completeness score: % of template fields filled (not "unknown")
- Correction rate: how often humans override audit findings
- Gap rate: how often post-audit capture logs a "prompt-gap"
- Contradiction discovery rate: how often an audit finds new contradictions
- Staleness at discovery: how stale were assumptions the audit uncovered

Trend detection over a sliding window (improving / stable / degrading).

Storage: feedback/prompt-scores.json
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
from synthesize.extract import load_all_audits, AuditFacts

UNKNOWN_MARKERS = {"unknown", "n/a", "—", "", "?", "none"}

# Fields we measure completeness across
COMPLETENESS_FIELDS = [
    "identity.repo_name",
    "identity.github_url",
    "identity.owners",
    "identity.prod_status",
    "identity.purpose",
    "tech_stack.languages",
    "tech_stack.frameworks",
    "tech_stack.build_tools",
    "tech_stack.runtime",
    "deployment.ci",
    "deployment.cd",
    "deployment.targets",
    "deployment.pipeline_files",
    "package.name",
    "package.registry",
    "package.version",
]


def _get_field_value(facts: AuditFacts, path: str) -> str:
    """Resolve a dotted path like 'identity.owners' on an AuditFacts."""
    parts = path.split(".")
    obj = facts
    for part in parts:
        obj = getattr(obj, part, "")
        if isinstance(obj, str):
            return obj
    return str(obj) if obj else ""


def _completeness(facts: AuditFacts) -> tuple[float, list[str]]:
    """Return (score 0-1, list of incomplete fields)."""
    filled = 0
    incomplete: list[str] = []
    for field_path in COMPLETENESS_FIELDS:
        val = _get_field_value(facts, field_path)
        if val.strip().lower() not in UNKNOWN_MARKERS:
            filled += 1
        else:
            incomplete.append(field_path)
    score = filled / len(COMPLETENESS_FIELDS) if COMPLETENESS_FIELDS else 0
    return score, incomplete


def _group_by_prompt(audit_state: dict, all_facts: dict[str, AuditFacts]) -> dict[str, list[str]]:
    """Group repo names by the prompt variant used."""
    groups: dict[str, list[str]] = defaultdict(list)
    for repo_name, state in audit_state.get("repos", {}).items():
        prompt_name = state.get("prompt_name", "default")
        prompt_file = f"prompts/{prompt_name}.md"
        groups[prompt_file].append(repo_name)
    return dict(groups)


def _trend(scores: list[float], window: int = 5) -> str:
    """Determine trend from recent scores. Needs at least 2 data points."""
    if len(scores) < 2:
        return "insufficient-data"
    recent = scores[-window:]
    if len(recent) < 2:
        return "insufficient-data"
    mid = len(recent) // 2
    first_half = sum(recent[:mid]) / max(mid, 1)
    second_half = sum(recent[mid:]) / max(len(recent) - mid, 1)
    diff = second_half - first_half
    if diff > 0.05:
        return "improving"
    elif diff < -0.05:
        return "degrading"
    return "stable"


def score_prompts(dry_run: bool = False) -> dict:
    """Score all prompt variants based on audit outcomes and feedback.

    Returns the full scores dict (also written to feedback/prompt-scores.json).
    """
    audit_state = get_state()
    all_facts = load_all_audits(use_cache=True)
    capture_log = load_capture_log()
    prompt_groups = _group_by_prompt(audit_state, all_facts)

    # Index captures by audit path
    captures_by_audit: dict[str, list[dict]] = defaultdict(list)
    for entry in capture_log:
        audit_key = entry.get("audit", "")
        for cap in entry.get("captures", []):
            captures_by_audit[audit_key].append(cap)

    # Load contradiction data to measure discovery rate
    contradictions_path = config.MAPS_DATA_DIR / "contradictions-and-ambiguities.json"
    contradiction_repos: set[str] = set()
    if contradictions_path.is_file():
        try:
            data = json.loads(contradictions_path.read_text())
            for item in data.get("items", []):
                for r in item.get("repos", []):
                    contradiction_repos.add(r)
        except (json.JSONDecodeError, OSError):
            pass

    scores: dict[str, dict] = {}

    for prompt_file, repo_names in prompt_groups.items():
        completeness_scores: list[float] = []
        all_incomplete: dict[str, int] = defaultdict(int)
        total_caps = 0
        gap_caps = 0
        correction_caps = 0
        repos_with_contradictions = 0

        for repo_name in repo_names:
            facts = all_facts.get(repo_name)
            if not facts:
                continue

            c_score, incomplete = _completeness(facts)
            completeness_scores.append(c_score)
            for field in incomplete:
                all_incomplete[field] += 1

            audit_key = f"audits/{repo_name}.md"
            caps = captures_by_audit.get(audit_key, [])
            total_caps += len(caps)
            gap_caps += sum(1 for c in caps if c.get("type") == "prompt-gap")
            correction_caps += sum(1 for c in caps if c.get("type") == "correction")

            if repo_name in contradiction_repos:
                repos_with_contradictions += 1

        n_audits = len(repo_names)
        avg_completeness = sum(completeness_scores) / max(len(completeness_scores), 1)
        correction_rate = correction_caps / max(n_audits, 1)
        gap_rate = gap_caps / max(n_audits, 1)
        contradiction_rate = repos_with_contradictions / max(n_audits, 1)

        # Find consistently low-completeness fields
        low_fields = sorted(
            [(f, cnt) for f, cnt in all_incomplete.items() if cnt > n_audits * 0.3],
            key=lambda x: -x[1],
        )

        scores[prompt_file] = {
            "audits_run": n_audits,
            "avg_completeness": round(avg_completeness, 3),
            "correction_rate": round(correction_rate, 3),
            "gap_rate": round(gap_rate, 3),
            "contradiction_discovery_rate": round(contradiction_rate, 3),
            "trend": _trend(completeness_scores),
            "low_completeness_fields": [
                {"field": f, "missing_in": cnt, "pct": round(cnt / max(n_audits, 1), 2)}
                for f, cnt in low_fields
            ],
            "repos": sorted(repo_names),
            "last_scored": datetime.now(timezone.utc).isoformat(),
        }

    if not dry_run:
        config.FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
        config.PROMPT_SCORES_PATH.write_text(
            json.dumps(scores, indent=2, sort_keys=True) + "\n"
        )

    return scores


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write scores file")
def main(dry_run: bool) -> None:
    """Score prompt effectiveness across all audits."""
    scores = score_prompts(dry_run=dry_run)

    click.echo(f"\n{'=' * 60}")
    click.echo("PROMPT EFFECTIVENESS SCORES")
    click.echo(f"{'=' * 60}")

    for prompt_file, s in sorted(scores.items()):
        click.echo(f"\n  {prompt_file}")
        click.echo(f"    Audits run:          {s['audits_run']}")
        click.echo(f"    Avg completeness:    {s['avg_completeness']:.1%}")
        click.echo(f"    Correction rate:     {s['correction_rate']:.1%}")
        click.echo(f"    Gap rate:            {s['gap_rate']:.1%}")
        click.echo(f"    Contradiction rate:  {s['contradiction_discovery_rate']:.1%}")
        click.echo(f"    Trend:               {s['trend']}")
        if s["low_completeness_fields"]:
            click.echo(f"    Weak fields:")
            for f in s["low_completeness_fields"]:
                click.echo(f"      - {f['field']} (missing in {f['pct']:.0%})")

    if dry_run:
        click.echo("\n  (dry run — no file written)")


if __name__ == "__main__":
    main()
