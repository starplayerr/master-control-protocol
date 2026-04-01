#!/usr/bin/env python3
"""Synthesis orchestrator.

Runs all synthesizers in the correct dependency order:
  1. Dependencies (others need the dep graph)
  2. Contradictions (uses dep graph context)
  3. Stale assumptions (uses dep graph + contradictions)
  4. Simplifications (uses all of the above)

Supports --only to run a single synthesizer, and --dry-run to preview.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthesize import dependencies, contradictions, stale_assumptions, simplifications


SYNTHESIZERS = {
    "dependencies": ("Dependency Graph Builder", dependencies.run),
    "contradictions": ("Contradiction Detector", contradictions.run),
    "stale-assumptions": ("Stale Assumption Scanner", stale_assumptions.run),
    "simplifications": ("Simplification Candidate Finder", simplifications.run),
}

RUN_ORDER = ["dependencies", "contradictions", "stale-assumptions", "simplifications"]


def _print_result(name: str, label: str, result: dict, elapsed: float) -> None:
    print(f"\n  {label}")
    print(f"  {'-' * len(label)}")

    if name == "dependencies":
        print(f"    Edges discovered: {result.get('edges_discovered', 0)}")
        print(f"    Edges after merge: {result.get('edges_merged', 0)}")
        cycles = result.get("cycles", [])
        if cycles:
            print(f"    Cycles: {len(cycles)}")
        risks = result.get("high_risk_nodes", [])
        if risks:
            for r in risks:
                print(f"    SPOF: {r['repo']} ({r['dependent_count']} dependents)")
    else:
        total = result.get("total_findings", 0)
        new = result.get("new_findings", 0)
        existing = result.get("existing_findings", 0)
        print(f"    Found: {total} ({new} new, {existing} pre-existing)")

    print(f"    Time: {elapsed:.1f}s")


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write changes")
@click.option(
    "--only",
    type=click.Choice(RUN_ORDER),
    default=None,
    help="Run only one synthesizer",
)
def main(dry_run: bool, only: str | None) -> None:
    """Run all synthesis scripts in dependency order."""
    order = [only] if only else RUN_ORDER

    print("=" * 60)
    print("MCP SYNTHESIS ENGINE")
    print("=" * 60)

    if dry_run:
        print("  (dry run mode — no files will be written)")

    total_start = time.time()
    summary: dict[str, dict] = {}

    for name in order:
        label, fn = SYNTHESIZERS[name]
        t0 = time.time()
        result = fn(dry_run=dry_run)
        elapsed = time.time() - t0
        summary[name] = result
        _print_result(name, label, result, elapsed)

    total_elapsed = time.time() - total_start

    # Summary
    print(f"\n{'=' * 60}")
    print(f"SYNTHESIS COMPLETE ({total_elapsed:.1f}s total)")
    print(f"{'=' * 60}")

    if "dependencies" in summary:
        r = summary["dependencies"]
        print(f"  Dependencies:    {r.get('edges_merged', 0)} edges")
    if "contradictions" in summary:
        r = summary["contradictions"]
        print(f"  Contradictions:  {r.get('total_findings', 0)} found ({r.get('new_findings', 0)} new)")
    if "stale-assumptions" in summary:
        r = summary["stale-assumptions"]
        print(f"  Stale items:     {r.get('total_findings', 0)} found ({r.get('new_findings', 0)} new)")
    if "simplifications" in summary:
        r = summary["simplifications"]
        print(f"  Simplifications: {r.get('total_findings', 0)} found ({r.get('new_findings', 0)} new)")


if __name__ == "__main__":
    main()
