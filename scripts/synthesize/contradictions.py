#!/usr/bin/env python3
"""Contradiction detector.

Cross-references audit facts to find conflicts between repos: version
skew, ownership inconsistencies, config conflicts, deployment conflicts,
documentation contradictions, and API contract mismatches.
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


def _next_id(existing_items: list[dict], prefix: str = "C") -> str:
    """Generate the next sequential ID like C-001, C-002, etc."""
    max_num = 0
    for item in existing_items:
        item_id = item.get("id", "")
        m = re.match(rf"{prefix}-(\d+)", item_id)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"{prefix}-{max_num + 1:03d}"


def _parse_version(dep_str: str) -> tuple[str, str]:
    """Extract (package_name, version) from strings like 'ruff==0.15.8'."""
    m = re.match(r"^([a-zA-Z0-9_-]+)\s*[><=!~]+\s*(.+)$", dep_str.strip())
    if m:
        return m.group(1).lower(), m.group(2).strip()
    return dep_str.strip().lower(), ""


def _normalise_owner(owner: str) -> str:
    """Normalise owner strings for comparison."""
    return owner.strip().lower().strip("@").replace(" ", "")


# ── Detection rules ──────────────────────────────────────────────────────────


def detect_version_conflicts(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find same package pinned to different versions across repos."""
    pkg_versions: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for repo, facts in all_facts.items():
        for dep in facts.outbound_deps:
            pkg_name, version = _parse_version(dep.get("dependency", ""))
            if version and pkg_name:
                pkg_versions[pkg_name].append((repo, version, facts.source_file))

    # Also check package.version for the producer
    for repo, facts in all_facts.items():
        if facts.package.name and facts.package.version:
            pkg_name = facts.package.name.lower()
            pkg_versions[pkg_name].append(
                (repo, facts.package.version.lstrip("v"), facts.source_file)
            )

    contradictions = []
    for pkg, entries in pkg_versions.items():
        versions_seen = {}
        for repo, ver, source in entries:
            versions_seen.setdefault(ver, []).append((repo, source))

        if len(versions_seen) > 1:
            repos_involved = []
            details_parts = []
            sources = set()
            for ver, repo_list in sorted(versions_seen.items()):
                for repo, source in repo_list:
                    repos_involved.append(repo)
                    sources.add(source)
                    details_parts.append(f"{repo} uses {pkg}=={ver}")

            contradictions.append({
                "category": "version-conflict",
                "summary": f"Package '{pkg}' has different versions across repos: "
                           + ", ".join(f"{v} ({', '.join(r for r, _ in rs)})"
                                       for v, rs in sorted(versions_seen.items())),
                "sources": sorted(sources),
                "repos": sorted(set(repos_involved)),
                "impact": "medium",
                "confidence": "high",
                "details": "; ".join(details_parts),
                "status": "active",
            })

    return contradictions


def detect_ownership_conflicts(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find inconsistent ownership claims across repos that share a GitHub org."""
    # Group by GitHub org extracted from URL
    org_repos: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for repo, facts in all_facts.items():
        url = facts.identity.github_url
        owner_raw = facts.identity.owners
        m = re.search(r"github\.com/([^/]+)/", url) if url else None
        org = m.group(1).lower() if m else ""
        if org and owner_raw:
            org_repos[org].append((repo, owner_raw))

    contradictions = []
    for org, entries in org_repos.items():
        raw_forms = set(raw for _, raw in entries)
        if len(raw_forms) > 1:
            contradictions.append({
                "category": "ownership-conflict",
                "summary": f"Repos in github.com/{org} use different owner formats: "
                           + ", ".join(f"'{raw}' ({repo})" for repo, raw in entries),
                "sources": sorted(set(
                    all_facts[repo].source_file for repo, _ in entries
                )),
                "repos": sorted(set(repo for repo, _ in entries)),
                "impact": "low",
                "confidence": "high",
                "details": f"Same GitHub org '{org}' has different ownership strings: "
                           + ", ".join(sorted(raw_forms)),
                "status": "active",
            })

    return contradictions


def detect_registry_conflicts(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find conflicting registry claims within a single repo or across repos."""
    contradictions = []

    for repo, facts in all_facts.items():
        pkg_registry = facts.package.registry.lower() if facts.package.registry else ""
        artifact_registries = set()
        for art in facts.artifacts:
            for field_key in ("registry", "destination", "name"):
                val = art.get(field_key, "").lower()
                if val:
                    artifact_registries.add(val)

        if pkg_registry and artifact_registries:
            # Check for Docker Hub vs GHCR type conflicts
            pkg_mentions_dockerhub = "docker hub" in pkg_registry or "docker" in pkg_registry
            art_mentions_ghcr = any("ghcr" in r for r in artifact_registries)
            art_mentions_dockerhub = any("docker hub" in r or "hub.docker" in r for r in artifact_registries)

            if pkg_mentions_dockerhub and art_mentions_ghcr and not art_mentions_dockerhub:
                contradictions.append({
                    "category": "deployment-conflict",
                    "summary": f"{repo}: Package Details mentions Docker Hub but Artifacts only reference GHCR",
                    "sources": [facts.source_file],
                    "repos": [repo],
                    "impact": "low",
                    "confidence": "medium",
                    "details": f"Package registry field says '{facts.package.registry}', "
                               f"but artifacts reference: {', '.join(sorted(artifact_registries))}",
                    "status": "active",
                })

    return contradictions


def detect_version_skew_vs_producer(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find consumers pinning a version behind the producer's current version."""
    producer_versions: dict[str, tuple[str, str]] = {}
    for repo, facts in all_facts.items():
        if facts.package.name and facts.package.version:
            producer_versions[facts.package.name.lower()] = (
                facts.package.version.lstrip("v"), repo
            )

    contradictions = []
    for repo, facts in all_facts.items():
        for dep in facts.outbound_deps:
            pkg_name, pinned_ver = _parse_version(dep.get("dependency", ""))
            if not pinned_ver or pkg_name not in producer_versions:
                continue

            prod_ver, prod_repo = producer_versions[pkg_name]
            if pinned_ver != prod_ver and prod_repo != repo:
                contradictions.append({
                    "category": "version-conflict",
                    "summary": f"{repo} pins {pkg_name}=={pinned_ver} but "
                               f"{prod_repo} is at version {prod_ver}",
                    "sources": sorted([facts.source_file, all_facts[prod_repo].source_file]),
                    "repos": sorted([repo, prod_repo]),
                    "impact": "medium",
                    "confidence": "high",
                    "details": f"Consumer {repo} depends on {pkg_name}=={pinned_ver}; "
                               f"producer {prod_repo} reports current version as {prod_ver}",
                    "status": "active",
                })

    return contradictions


def detect_toolchain_conflicts(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find repos using different versions of shared toolchains (Rust, Node, etc)."""
    toolchain_versions: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for repo, facts in all_facts.items():
        for cfg in facts.configs:
            config_name = cfg.get("config", "").lower()
            notes = cfg.get("notes", "")

            if "rust-toolchain" in config_name or "rust toolchain" in config_name:
                # Extract version from notes
                m = re.search(r"(\d+\.\d+(?:\.\d+)?)", notes)
                if m:
                    toolchain_versions["rust"].append(
                        (repo, m.group(1), facts.source_file)
                    )

    contradictions = []
    for tool, entries in toolchain_versions.items():
        versions = {}
        for repo, ver, source in entries:
            versions.setdefault(ver, []).append((repo, source))

        if len(versions) > 1:
            sources = set()
            repos = []
            for ver, repo_list in versions.items():
                for repo, source in repo_list:
                    repos.append(repo)
                    sources.add(source)

            contradictions.append({
                "category": "config-conflict",
                "summary": f"{tool.title()} toolchain version differs: "
                           + ", ".join(f"{v} ({', '.join(r for r, _ in rs)})"
                                       for v, rs in sorted(versions.items())),
                "sources": sorted(sources),
                "repos": sorted(set(repos)),
                "impact": "medium",
                "confidence": "medium",
                "details": f"Different {tool} toolchain versions may cause build inconsistencies",
                "status": "active",
            })

    return contradictions


def detect_deployment_conflicts(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find repos claiming the same deployment target via different mechanisms."""
    target_map: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for repo, facts in all_facts.items():
        targets_str = facts.deployment.targets
        if targets_str:
            for target in re.split(r"[,;]", targets_str):
                target = target.strip().lower()
                if target:
                    target_map[target].append((
                        repo, facts.deployment.cd, facts.source_file
                    ))

    contradictions = []
    for target, entries in target_map.items():
        cd_systems = {}
        for repo, cd, source in entries:
            cd_systems.setdefault(cd.lower(), []).append((repo, source))

        # Only flag if truly different CD systems for same target
        if len(cd_systems) > 1 and all(len(repos) >= 1 for repos in cd_systems.values()):
            sources = set()
            repos = []
            for cd, repo_list in cd_systems.items():
                for repo, source in repo_list:
                    repos.append(repo)
                    sources.add(source)

            if len(set(repos)) > 1:
                contradictions.append({
                    "category": "deployment-conflict",
                    "summary": f"Target '{target}' deployed by different CD systems: "
                               + ", ".join(f"{cd} ({', '.join(r for r, _ in rs)})"
                                           for cd, rs in cd_systems.items()),
                    "sources": sorted(sources),
                    "repos": sorted(set(repos)),
                    "impact": "low",
                    "confidence": "medium",
                    "details": f"Multiple repos target '{target}' using different CD pipelines",
                    "status": "active",
                })

    return contradictions


def detect_secret_naming_conflicts(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find same secret name used for different purposes across repos."""
    secret_usage: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for repo, facts in all_facts.items():
        for sec in facts.secrets:
            name = sec.get("name", "").strip()
            usage = sec.get("usage", "").strip()
            if name and name != "GITHUB_TOKEN":
                secret_usage[name].append((repo, usage, facts.source_file))

    contradictions = []
    for secret, entries in secret_usage.items():
        usages = set(usage for _, usage, _ in entries)
        if len(entries) > 1 and len(usages) > 1:
            contradictions.append({
                "category": "config-conflict",
                "summary": f"Secret '{secret}' used for different purposes: "
                           + ", ".join(f"'{usage}' in {repo}" for repo, usage, _ in entries),
                "sources": sorted(set(s for _, _, s in entries)),
                "repos": sorted(set(r for r, _, _ in entries)),
                "impact": "medium",
                "confidence": "medium",
                "details": f"Same credential name with different stated purposes may indicate "
                           f"confusion about its actual scope",
                "status": "active",
            })

    return contradictions


# ── Aggregation and dedup ────────────────────────────────────────────────────


def _dedup_key(item: dict) -> str:
    """Generate a dedup key from category + sorted repos."""
    return f"{item['category']}:{','.join(sorted(item.get('repos', [])))}"


def run_all_detectors(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Run every detector and return deduplicated findings."""
    raw: list[dict] = []
    raw.extend(detect_version_conflicts(all_facts))
    raw.extend(detect_version_skew_vs_producer(all_facts))
    raw.extend(detect_ownership_conflicts(all_facts))
    raw.extend(detect_registry_conflicts(all_facts))
    raw.extend(detect_toolchain_conflicts(all_facts))
    raw.extend(detect_deployment_conflicts(all_facts))
    raw.extend(detect_secret_naming_conflicts(all_facts))

    # Dedup: prefer version-skew-vs-producer over generic version-conflict
    seen: dict[str, dict] = {}
    for item in raw:
        key = _dedup_key(item)
        if key in seen:
            existing = seen[key]
            if item["confidence"] == "high" and existing["confidence"] != "high":
                seen[key] = item
        else:
            seen[key] = item

    return list(seen.values())


# ── Prose update ─────────────────────────────────────────────────────────────


def update_prose(items: list[dict]) -> None:
    """Append new contradictions to the prose map's Active Contradictions table."""
    prose_path = config.MAPS_DIR / "contradictions-and-ambiguities.md"
    text = prose_path.read_text()

    # Find the Active Contradictions table
    marker = "| C-001 | | | high · medium · low | | |"
    if marker not in text:
        return

    new_rows = []
    for item in items:
        row = (
            f"| {item['id']} "
            f"| {', '.join(item['repos'])} "
            f"| {item['summary']} "
            f"| {item['impact']} "
            f"| Verify and resolve "
            f"| {', '.join(item['sources'])} |"
        )
        new_rows.append(row)

    if new_rows:
        replacement = "\n".join(new_rows)
        text = text.replace(marker, replacement)

        post = frontmatter.loads(text)
        post.metadata["freshness"] = "current"
        post.metadata["last_updated"] = date.today().isoformat()
        prose_path.write_text(frontmatter.dumps(post) + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────


def run(dry_run: bool = False) -> dict:
    """Run the contradiction detector. Returns summary stats."""
    all_facts = load_all_audits()
    findings = run_all_detectors(all_facts)

    data_path = config.MAPS_DATA_DIR / "contradictions-and-ambiguities.json"
    if data_path.is_file():
        existing = json.loads(data_path.read_text())
    else:
        existing = {"schema_version": "1.0", "items": []}

    existing_items = existing.get("items", [])
    existing_summaries = {i.get("summary") for i in existing_items}

    new_items = []
    for f in findings:
        if f["summary"] not in existing_summaries:
            f["id"] = _next_id(existing_items + new_items)
            f["detected_date"] = date.today().isoformat()
            new_items.append(f)

    all_items = existing_items + new_items

    if not dry_run:
        existing["items"] = all_items
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
    """Detect contradictions across audit reports."""
    result = run(dry_run=dry_run)
    print(f"\nContradiction Detector")
    print(f"{'=' * 40}")
    print(f"  Total findings: {result['total_findings']}")
    print(f"  New:            {result['new_findings']}")
    print(f"  Pre-existing:   {result['existing_findings']}")

    if result["items"]:
        print(f"\n  All contradictions:")
        for item in result["items"]:
            print(f"    {item['id']}: [{item['category']}] {item['summary']}")
            print(f"          repos: {', '.join(item.get('repos', []))}")
            print(f"          impact: {item['impact']}, confidence: {item['confidence']}")
    else:
        print(f"\n  WARNING: Zero contradictions found across "
              f"{len(result.get('items', []))} related repos.")
        print(f"  Either detection logic is too conservative or audits lack detail.")

    if dry_run:
        print(f"\n  (dry run — no files written)")


if __name__ == "__main__":
    main()
