#!/usr/bin/env python3
"""History synthesis integration.

Feeds git-history findings into existing map data structures:
  - Undocumented coupling -> contradictions-and-ambiguities.json
  - Knowledge silos -> missing-docs.json
  - Dormant repos -> stale-assumptions.json
  - Owner mismatches -> contradictions-and-ambiguities.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config


# ── ID generation (matches synthesize/contradictions.py pattern) ─────────────


def _next_id(existing_items: list[dict], prefix: str) -> str:
    max_num = 0
    for item in existing_items:
        item_id = item.get("id", "")
        m = re.match(rf"{prefix}-(\d+)", item_id)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"{prefix}-{max_num + 1:03d}"


def _load_json(path: Path, default_key: str) -> dict:
    if path.is_file():
        return json.loads(path.read_text())
    return {"schema_version": "1.0", default_key: []}


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


# ── Finding generators ───────────────────────────────────────────────────────


def _coupling_findings() -> list[dict]:
    """Generate contradiction entries from undocumented coupling pairs."""
    coupling_path = config.MAPS_DATA_DIR / "co-change-coupling.json"
    if not coupling_path.is_file():
        return []

    data = json.loads(coupling_path.read_text())
    findings = []

    for pair in data.get("pairs", []):
        if pair.get("known_dependency"):
            continue
        if pair.get("coupling_score", 0) < 0.3:
            continue

        findings.append({
            "category": "undocumented-dependency",
            "summary": (
                f"Git history shows {pair['repo_a']} and {pair['repo_b']} "
                f"co-change {pair['co_changes']} times (coupling score: "
                f"{pair['coupling_score']}) but no documented dependency exists"
            ),
            "sources": ["maps/data/co-change-coupling.json"],
            "repos": sorted([pair["repo_a"], pair["repo_b"]]),
            "impact": "medium" if pair["coupling_score"] >= 0.5 else "low",
            "confidence": "medium",
            "details": (
                f"Within a {data.get('window_hours', 48)}h window over "
                f"{data.get('analysis_period_months', 6)} months, these repos "
                f"had {pair['co_changes']} co-changes. Shared authors: "
                f"{', '.join(pair.get('shared_authors', [])) or 'none'}"
            ),
            "status": "active",
        })

    return findings


def _owner_mismatch_findings() -> list[dict]:
    """Generate contradiction entries from owner mismatches."""
    knowledge_path = config.MAPS_DATA_DIR / "knowledge-distribution.json"
    if not knowledge_path.is_file():
        return []

    data = json.loads(knowledge_path.read_text())
    findings = []

    for mismatch in data.get("owner_mismatches", []):
        findings.append({
            "category": "owner-mismatch",
            "summary": (
                f"{mismatch['repo']}: listed owner '{mismatch['listed_owner']}' "
                f"does not appear in top git contributors "
                f"({', '.join(mismatch['top_contributors'])})"
            ),
            "sources": ["maps/data/knowledge-distribution.json"],
            "repos": [mismatch["repo"]],
            "impact": "low",
            "confidence": "medium",
            "details": (
                f"INVENTORY.md lists '{mismatch['listed_owner']}' as owner, "
                f"but the top committers by volume and recency are: "
                f"{', '.join(mismatch['top_contributors'])}"
            ),
            "status": "active",
        })

    return findings


def _knowledge_silo_findings() -> list[dict]:
    """Generate missing-docs entries from knowledge silos."""
    knowledge_path = config.MAPS_DATA_DIR / "knowledge-distribution.json"
    if not knowledge_path.is_file():
        return []

    data = json.loads(knowledge_path.read_text())
    findings = []

    for repo_name, repo_data in data.get("repos", {}).items():
        if repo_data.get("bus_factor", 99) <= 1:
            sole_experts = repo_data.get("sole_experts", [])
            expert_paths = [e["path"] for e in sole_experts[:5]]

            findings.append({
                "category": "knowledge-silo",
                "summary": (
                    f"{repo_name} has bus factor of {repo_data['bus_factor']} — "
                    f"critical paths need documentation"
                ),
                "sources": ["maps/data/knowledge-distribution.json"],
                "repos": [repo_name],
                "impact": "high",
                "confidence": "high",
                "details": (
                    f"Sole-expert files: {', '.join(expert_paths) or 'none detected'}. "
                    f"If the primary contributor becomes unavailable, "
                    f"institutional knowledge is lost."
                ),
                "status": "active",
            })

    return findings


def _dormancy_findings() -> list[dict]:
    """Generate stale-assumption entries from dormant repos."""
    temporal_path = config.MAPS_DATA_DIR / "temporal-patterns.json"
    if not temporal_path.is_file():
        return []

    data = json.loads(temporal_path.read_text())
    findings = []

    for dormant in data.get("dormant_repos", []):
        findings.append({
            "category": "dormant-repo",
            "assumption": (
                f"{dormant['repo']} is actively maintained"
            ),
            "reality": (
                f"{dormant['status']}. Last activity: "
                f"{dormant.get('last_activity', 'unknown')}"
            ),
            "repos": [dormant["repo"]],
            "confidence": "high",
            "status": "active",
            "source": "maps/data/temporal-patterns.json",
        })

    return findings


# ── Merge into existing data ─────────────────────────────────────────────────


def _merge_into_contradictions(
    new_findings: list[dict],
    dry_run: bool,
) -> tuple[int, int]:
    """Merge findings into contradictions-and-ambiguities.json. Returns (total, new)."""
    path = config.MAPS_DATA_DIR / "contradictions-and-ambiguities.json"
    data = _load_json(path, "items")
    existing = data.get("items", [])
    existing_summaries = {item.get("summary") for item in existing}

    added = []
    for f in new_findings:
        if f["summary"] not in existing_summaries:
            f["id"] = _next_id(existing + added, "C")
            f["detected_date"] = date.today().isoformat()
            added.append(f)
            existing_summaries.add(f["summary"])

    if added and not dry_run:
        data["items"] = existing + added
        _write_json(path, data)

    return len(existing) + len(added), len(added)


def _merge_into_missing_docs(
    new_findings: list[dict],
    dry_run: bool,
) -> tuple[int, int]:
    """Merge findings into missing-docs.json. Returns (total, new)."""
    path = config.MAPS_DATA_DIR / "missing-docs.json"
    data = _load_json(path, "items")
    existing = data.get("items", [])
    existing_summaries = {item.get("summary") for item in existing}

    added = []
    for f in new_findings:
        if f["summary"] not in existing_summaries:
            f["id"] = _next_id(existing + added, "MD")
            f["detected_date"] = date.today().isoformat()
            added.append(f)
            existing_summaries.add(f["summary"])

    if added and not dry_run:
        data["items"] = existing + added
        _write_json(path, data)

    return len(existing) + len(added), len(added)


def _merge_into_stale_assumptions(
    new_findings: list[dict],
    dry_run: bool,
) -> tuple[int, int]:
    """Merge findings into stale-assumptions.json. Returns (total, new)."""
    path = config.MAPS_DATA_DIR / "stale-assumptions.json"
    data = _load_json(path, "items")
    existing = data.get("items", [])
    existing_assumptions = {item.get("assumption") for item in existing}

    added = []
    for f in new_findings:
        if f["assumption"] not in existing_assumptions:
            f["id"] = _next_id(existing + added, "S")
            f["detected_date"] = date.today().isoformat()
            added.append(f)
            existing_assumptions.add(f["assumption"])

    if added and not dry_run:
        data["items"] = existing + added
        _write_json(path, data)

    return len(existing) + len(added), len(added)


# ── Main ─────────────────────────────────────────────────────────────────────


def run(dry_run: bool = False) -> dict:
    """Integrate all history findings into existing maps."""
    # Gather findings
    coupling = _coupling_findings()
    owner_mismatches = _owner_mismatch_findings()
    silos = _knowledge_silo_findings()
    dormancy = _dormancy_findings()

    contradiction_findings = coupling + owner_mismatches

    # Merge
    c_total, c_new = _merge_into_contradictions(contradiction_findings, dry_run)
    md_total, md_new = _merge_into_missing_docs(silos, dry_run)
    s_total, s_new = _merge_into_stale_assumptions(dormancy, dry_run)

    return {
        "contradictions": {"total": c_total, "new": c_new},
        "missing_docs": {"total": md_total, "new": md_new},
        "stale_assumptions": {"total": s_total, "new": s_new},
        "total_new": c_new + md_new + s_new,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write changes")
def main(dry_run: bool) -> None:
    """Integrate history findings into existing maps."""
    result = run(dry_run=dry_run)

    print(f"\nHistory Integration")
    print(f"{'=' * 40}")
    print(f"  Contradictions: {result['contradictions']['total']} "
          f"({result['contradictions']['new']} new from history)")
    print(f"  Missing docs:   {result['missing_docs']['total']} "
          f"({result['missing_docs']['new']} new from history)")
    print(f"  Stale items:    {result['stale_assumptions']['total']} "
          f"({result['stale_assumptions']['new']} new from history)")
    print(f"\n  Total new findings integrated: {result['total_new']}")

    if dry_run:
        print(f"\n  (dry run — no files written)")


if __name__ == "__main__":
    main()
