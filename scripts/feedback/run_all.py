#!/usr/bin/env python3
"""Feedback loop orchestrator.

Runs all feedback subsystems in dependency order:
  1. Prompt scoring (needs capture log + audit state)
  2. Prompt evolution (needs prompt scores + capture log)
  3. Map quality scoring (needs audits + capture log)
  4. Dashboard data (needs all of the above)

The capture step runs separately, integrated into the audit pipeline.
To run capture manually: python scripts/feedback/capture.py --audit <path>

Supports --only to run a single subsystem, and --dry-run to preview.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from feedback import prompt_score, evolve_prompt, map_quality, dashboard_data

SUBSYSTEMS = {
    "prompt-scores": ("Prompt Effectiveness Scorer", prompt_score.score_prompts),
    "evolve-prompts": ("Prompt Evolution Engine", evolve_prompt.evolve_prompts),
    "map-quality": ("Map Quality Scorer", map_quality.score_maps),
    "dashboard": ("Dashboard Data Generator", dashboard_data.generate_dashboard),
}

RUN_ORDER = ["prompt-scores", "evolve-prompts", "map-quality", "dashboard"]


def _print_result(name: str, label: str, result: dict, elapsed: float) -> None:
    print(f"\n  {label}")
    print(f"  {'-' * len(label)}")

    if name == "prompt-scores":
        for prompt_file, scores in result.items():
            print(f"    {prompt_file}: {scores.get('avg_completeness', 0):.0%} complete, trend={scores.get('trend', '?')}")
    elif name == "evolve-prompts":
        print(f"    Gaps analyzed: {result.get('total_gaps', 0)}")
        print(f"    Proposals generated: {result.get('proposals', 0)}")
    elif name == "map-quality":
        for map_file, scores in result.items():
            grade = scores.get("overall_quality", "?")
            print(f"    [{grade}] {map_file}")
    elif name == "dashboard":
        pus = result.get("platform_understanding_score", 0)
        print(f"    Platform Understanding Score: {pus:.1%}")

    print(f"    Time: {elapsed:.1f}s")


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write any files")
@click.option(
    "--only",
    type=click.Choice(RUN_ORDER),
    default=None,
    help="Run only one subsystem",
)
@click.option("--use-llm", is_flag=True, help="Use LLM for prompt evolution clustering")
def main(dry_run: bool, only: str | None, use_llm: bool) -> None:
    """Run all feedback loop subsystems in dependency order."""
    order = [only] if only else RUN_ORDER

    print("=" * 60)
    print("MCP FEEDBACK LOOP ENGINE")
    print("=" * 60)

    if dry_run:
        print("  (dry run mode — no files will be written)")

    total_start = time.time()
    summary: dict[str, dict] = {}

    for name in order:
        label, fn = SUBSYSTEMS[name]
        t0 = time.time()

        if name == "evolve-prompts":
            result = fn(use_llm=use_llm, dry_run=dry_run)
        else:
            result = fn(dry_run=dry_run)

        elapsed = time.time() - t0
        summary[name] = result
        _print_result(name, label, result, elapsed)

    total_elapsed = time.time() - total_start

    print(f"\n{'=' * 60}")
    print(f"FEEDBACK LOOP COMPLETE ({total_elapsed:.1f}s total)")
    print(f"{'=' * 60}")

    if "dashboard" in summary:
        pus = summary["dashboard"].get("platform_understanding_score", 0)
        print(f"  Platform Understanding Score: {pus:.1%}")


if __name__ == "__main__":
    main()
