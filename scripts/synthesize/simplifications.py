#!/usr/bin/env python3
"""Simplification candidate finder.

Identifies concrete opportunities to reduce platform complexity:
duplicate functionality, library fragmentation, dead repos,
consolidation candidates, config sprawl, and pipeline redundancy.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import click
import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from synthesize.extract import AuditFacts, load_all_audits


# ── Helpers ──────────────────────────────────────────────────────────────────


def _next_id(existing: list[dict], prefix: str = "SIM") -> str:
    max_num = 0
    for item in existing:
        m = re.match(rf"{prefix}-?(\d+)", item.get("id", ""))
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"{prefix}-{max_num + 1:03d}"


def _tokenise(text: str) -> set[str]:
    """Split text into lowercased tokens for overlap comparison."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


# ── Detection rules ──────────────────────────────────────────────────────────


def detect_thin_wrappers(
    all_facts: dict[str, AuditFacts],
    dep_edges: list[dict],
) -> list[dict]:
    """Find repos that are thin wrappers around another repo.

    Heuristics: few outbound deps (1-3), most/all are to a single parent repo,
    few artifacts, purpose statement heavily references the parent.
    """
    candidates = []

    for repo, facts in all_facts.items():
        if len(facts.outbound_deps) > 4:
            continue

        parent_counts: dict[str, int] = defaultdict(int)
        for edge in dep_edges:
            if edge.get("to") == repo:
                parent_counts[edge["from"]] += 1

        if not parent_counts:
            continue

        primary_parent = max(parent_counts, key=parent_counts.get)
        dep_on_parent = parent_counts[primary_parent]
        total_deps = len(facts.outbound_deps)

        if total_deps == 0:
            continue

        parent_dep_ratio = dep_on_parent / max(total_deps, 1)
        purpose_tokens = _tokenise(facts.identity.purpose)
        parent_tokens = _tokenise(primary_parent)
        purpose_mentions_parent = bool(parent_tokens & purpose_tokens)

        # Score: high ratio of deps on parent + few own artifacts + purpose references parent
        is_wrapper = (
            parent_dep_ratio >= 0.3
            and len(facts.artifacts) <= 2
            and purpose_mentions_parent
        )

        if is_wrapper:
            candidates.append({
                "category": "consolidation-candidate",
                "title": f"{repo} is a thin wrapper around {primary_parent}",
                "description": (
                    f"{repo} has {total_deps} outbound deps, "
                    f"{dep_on_parent} of which point to {primary_parent}. "
                    f"Purpose: '{facts.identity.purpose}'. "
                    f"Could potentially be consolidated into {primary_parent} or maintained "
                    f"as a minimal adapter."
                ),
                "repos": sorted([repo, primary_parent]),
                "effort": "medium",
                "risk": "low",
                "impact": "low",
                "tier": "medium-effort",
            })

    return candidates


def detect_config_sprawl(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find config sources referenced across many repos."""
    config_usage: dict[str, list[str]] = defaultdict(list)

    for repo, facts in all_facts.items():
        for cfg in facts.configs:
            source = cfg.get("source", "").strip()
            config_name = cfg.get("config", "").strip()
            if source:
                config_usage[source.lower()].append(repo)
            if config_name:
                config_usage[config_name.lower()].append(repo)

    candidates = []
    for config_key, repos in config_usage.items():
        unique_repos = sorted(set(repos))
        if len(unique_repos) >= 3:
            candidates.append({
                "category": "config-sprawl",
                "title": f"Config '{config_key}' referenced in {len(unique_repos)} repos",
                "description": (
                    f"The config source/key '{config_key}' appears in {len(unique_repos)} "
                    f"repos ({', '.join(unique_repos)}). Consider centralising this "
                    f"configuration to reduce duplication and drift risk."
                ),
                "repos": unique_repos,
                "effort": "low",
                "risk": "low",
                "impact": "medium",
                "tier": "quick-win",
            })

    return candidates


def detect_pipeline_redundancy(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find repos with very similar CI/CD setups."""
    ci_cd_profiles: dict[str, list[str]] = defaultdict(list)

    for repo, facts in all_facts.items():
        profile = f"{facts.deployment.ci}|{facts.deployment.cd}".lower()
        ci_cd_profiles[profile].append(repo)

    candidates = []
    for profile, repos in ci_cd_profiles.items():
        if len(repos) >= 3 and profile != "|":
            ci, cd = profile.split("|")
            candidates.append({
                "category": "pipeline-redundancy",
                "title": f"{len(repos)} repos share CI/CD pattern: {ci}/{cd}",
                "description": (
                    f"Repos {', '.join(repos)} all use {ci} for CI and {cd} for CD. "
                    f"Consider a shared workflow template or reusable action to reduce "
                    f"maintenance overhead."
                ),
                "repos": sorted(repos),
                "effort": "medium",
                "risk": "low",
                "impact": "medium",
                "tier": "medium-effort",
            })

    return candidates


def detect_library_fragmentation(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find same-language repos using different build tools."""
    lang_tools: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    for repo, facts in all_facts.items():
        langs = [l.strip().lower() for l in facts.tech_stack.languages.split(",")]
        tools = [t.strip().lower() for t in facts.tech_stack.build_tools.split(",")]
        for lang in langs:
            if lang:
                for tool in tools:
                    if tool:
                        lang_tools[lang][tool].append(repo)

    candidates = []
    for lang, tools in lang_tools.items():
        if len(tools) >= 2:
            all_repos = set()
            for repos in tools.values():
                all_repos.update(repos)

            if len(all_repos) >= 2:
                tool_summary = ", ".join(
                    f"{tool} ({', '.join(repos)})" for tool, repos in sorted(tools.items())
                )
                candidates.append({
                    "category": "library-fragmentation",
                    "title": f"{lang.title()} repos use different build tools",
                    "description": f"Build tool fragmentation for {lang}: {tool_summary}",
                    "repos": sorted(all_repos),
                    "effort": "high",
                    "risk": "medium",
                    "impact": "low",
                    "tier": "major-structural",
                })

    return candidates


def detect_duplicate_functionality(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find repos with highly overlapping purposes."""
    candidates = []
    repos = list(all_facts.keys())

    for i, repo_a in enumerate(repos):
        for repo_b in repos[i + 1:]:
            facts_a = all_facts[repo_a]
            facts_b = all_facts[repo_b]

            purpose_a = _tokenise(facts_a.identity.purpose)
            purpose_b = _tokenise(facts_b.identity.purpose)

            if not purpose_a or not purpose_b:
                continue

            overlap = purpose_a & purpose_b
            union = purpose_a | purpose_b
            similarity = len(overlap) / len(union) if union else 0

            # Also check tech stack overlap
            lang_a = _tokenise(facts_a.tech_stack.languages)
            lang_b = _tokenise(facts_b.tech_stack.languages)
            lang_overlap = len(lang_a & lang_b) / max(len(lang_a | lang_b), 1)

            if similarity > 0.5 and lang_overlap > 0.3:
                candidates.append({
                    "category": "duplicate-functionality",
                    "title": f"{repo_a} and {repo_b} have overlapping purposes",
                    "description": (
                        f"Purpose overlap: {similarity:.0%}. "
                        f"'{facts_a.identity.purpose}' vs '{facts_b.identity.purpose}'. "
                        f"Language overlap: {lang_overlap:.0%}."
                    ),
                    "repos": sorted([repo_a, repo_b]),
                    "effort": "high",
                    "risk": "high",
                    "impact": "medium",
                    "tier": "major-structural",
                })

    return candidates


# ── Scoring and aggregation ──────────────────────────────────────────────────

TIER_ORDER = {"quick-win": 0, "medium-effort": 1, "major-structural": 2}
IMPACT_ORDER = {"high": 0, "medium": 1, "low": 2}


def _sort_key(item: dict) -> tuple:
    return (
        TIER_ORDER.get(item.get("tier", ""), 9),
        IMPACT_ORDER.get(item.get("impact", ""), 9),
    )


def run_all_detectors(
    all_facts: dict[str, AuditFacts],
    dep_edges: list[dict],
) -> list[dict]:
    raw: list[dict] = []
    raw.extend(detect_thin_wrappers(all_facts, dep_edges))
    raw.extend(detect_config_sprawl(all_facts))
    raw.extend(detect_pipeline_redundancy(all_facts))
    raw.extend(detect_library_fragmentation(all_facts))
    raw.extend(detect_duplicate_functionality(all_facts))

    # Dedup by title
    seen: set[str] = set()
    deduped = []
    for item in raw:
        if item["title"] not in seen:
            seen.add(item["title"])
            deduped.append(item)

    return sorted(deduped, key=_sort_key)


# ── Prose update ─────────────────────────────────────────────────────────────


def update_prose(items: list[dict]) -> None:
    prose_path = config.MAPS_DIR / "candidate-simplifications.md"
    text = prose_path.read_text()

    marker = "| X-001 | | | | 1 · 2 · 3 | high · medium · low | proposed · approved · in progress · done | |"
    if marker in text and items:
        rows = []
        for item in items:
            tier_num = {"quick-win": "1", "medium-effort": "2", "major-structural": "3"}.get(
                item.get("tier", ""), "?"
            )
            rows.append(
                f"| {item['id']} "
                f"| {item['title']} "
                f"| {item['category']} "
                f"| {', '.join(item.get('repos', []))} "
                f"| {tier_num} "
                f"| {item.get('impact', 'unknown')} "
                f"| proposed "
                f"| synthesize/simplifications |"
            )
        text = text.replace(marker, "\n".join(rows))

    post = frontmatter.loads(text)
    post.metadata["freshness"] = "current"
    post.metadata["last_updated"] = date.today().isoformat()
    prose_path.write_text(frontmatter.dumps(post) + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────


def run(dry_run: bool = False) -> dict:
    all_facts = load_all_audits()

    dep_path = config.MAPS_DATA_DIR / "dependency-matrix.json"
    if dep_path.is_file():
        dep_edges = json.loads(dep_path.read_text()).get("edges", [])
    else:
        dep_edges = []

    findings = run_all_detectors(all_facts, dep_edges)

    data_path = config.MAPS_DATA_DIR / "candidate-simplifications.json"
    if data_path.is_file():
        existing = json.loads(data_path.read_text())
    else:
        existing = {"schema_version": "1.0", "candidates": []}

    existing_items = existing.get("candidates", [])
    existing_titles = {i.get("title") for i in existing_items}

    new_items = []
    for f in findings:
        if f["title"] not in existing_titles:
            f["id"] = _next_id(existing_items + new_items)
            f["detected_date"] = date.today().isoformat()
            new_items.append(f)

    all_items = existing_items + new_items

    if not dry_run:
        existing["candidates"] = all_items
        data_path.write_text(json.dumps(existing, indent=2) + "\n")
        update_prose(all_items)

    return {
        "total_findings": len(findings),
        "new_findings": len(new_items),
        "existing_findings": len(existing_items),
        "items": all_items,
    }


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write changes")
def main(dry_run: bool) -> None:
    """Find simplification candidates across audit reports."""
    result = run(dry_run=dry_run)
    print(f"\nSimplification Candidate Finder")
    print(f"{'=' * 40}")
    print(f"  Total findings: {result['total_findings']}")
    print(f"  New:            {result['new_findings']}")
    print(f"  Pre-existing:   {result['existing_findings']}")

    if result["items"]:
        print(f"\n  All candidates (sorted by tier):")
        for item in result["items"]:
            print(f"    {item['id']}: [{item['tier']}] {item['title']}")
            print(f"          repos: {', '.join(item.get('repos', []))}")
            print(f"          effort: {item['effort']}, risk: {item['risk']}, impact: {item['impact']}")
    else:
        print(f"\n  WARNING: Zero simplification candidates found.")

    if dry_run:
        print(f"\n  (dry run — no files written)")


if __name__ == "__main__":
    main()
