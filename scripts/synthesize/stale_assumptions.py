#!/usr/bin/env python3
"""Stale assumption scanner.

Identifies assumptions baked into repos that may no longer be true:
dead references, ghost dependencies, deprecated patterns, outdated
versions, stale documentation, and orphan configs.
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


def _next_id(existing: list[dict], prefix: str = "S") -> str:
    max_num = 0
    for item in existing:
        m = re.match(rf"{prefix}-(\d+)", item.get("id", ""))
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"{prefix}-{max_num + 1:03d}"


# Known deprecated libraries/patterns — configurable
DEPRECATED_PATTERNS: list[dict] = [
    {
        "pattern": r"ruff[_-]lsp",
        "reason": "ruff-lsp is deprecated in favour of Ruff's native language server",
        "category": "deprecated-pattern",
    },
    {
        "pattern": r"python[_\s]*3\.[89]\b",
        "reason": "Python 3.8/3.9 are end-of-life or nearing EOL",
        "category": "deprecated-pattern",
    },
]


# ── Detection rules ──────────────────────────────────────────────────────────


def detect_dead_references(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find repos that reference other repos/services not in any audit."""
    known_repos = set(all_facts.keys())
    known_lower = {r.lower() for r in known_repos}

    findings = []

    for repo, facts in all_facts.items():
        # Check inbound consumers
        for inb in facts.inbound_deps:
            consumer = inb.get("consumer", "")
            consumer_clean = re.split(r"\s", consumer)[0].strip().lower()
            consumer_clean = re.sub(r"^[a-zA-Z0-9_-]+/", "", consumer_clean)

            if consumer_clean and consumer_clean not in known_lower and len(consumer_clean) > 2:
                # Skip generic descriptions that aren't repo names
                generic = {
                    "unknown", "users", "workflows", "developers", "projects",
                    "end", "tools", "other", "python", "github", "actions",
                    "ci/cd", "major", "anyone", "pre-commit", "prek", "vs",
                }
                if consumer_clean in generic:
                    continue
                # Skip multi-word consumer descriptions
                if " " in consumer.strip():
                    continue
                is_repo_like = re.match(r"^[a-z0-9][-a-z0-9_.]*$", consumer_clean)
                if is_repo_like:
                    findings.append({
                        "category": "dead-reference",
                        "assumption": f"{repo} claims '{consumer}' depends on it",
                        "reality": f"No audit exists for '{consumer}' — cannot verify this consumer",
                        "repos": [repo],
                        "confidence": "needs-verification",
                        "status": "active",
                        "source": facts.source_file,
                    })

        # Check config sources that reference external repos
        for cfg in facts.configs:
            source = cfg.get("source", "")
            notes = cfg.get("notes", "")
            combined = f"{source} {notes}".lower()

            # Look for repo-like references: astral-sh/something, github.com/org/repo
            for m in re.finditer(r"(?:astral-sh|github\.com)/([a-z0-9_-]+)", combined):
                ref_name = m.group(1).lower()
                if ref_name not in known_lower and ref_name != repo.lower():
                    findings.append({
                        "category": "dead-reference",
                        "assumption": f"{repo} config references '{m.group(0)}'",
                        "reality": f"No audit exists for '{ref_name}'",
                        "repos": [repo],
                        "confidence": "needs-verification",
                        "status": "active",
                        "source": facts.source_file,
                    })

    return findings


def detect_ghost_dependencies(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find asymmetric dependency claims between repos."""
    known_repos = set(all_facts.keys())
    findings = []

    for repo, facts in all_facts.items():
        # Check: repo A says B depends on it, but B doesn't list A as outbound
        for inb in facts.inbound_deps:
            consumer = inb.get("consumer", "").strip()
            consumer_norm = re.sub(r"^[a-zA-Z0-9_-]+/", "", consumer).lower()

            # Find the matching audited repo
            matched_repo = None
            for kr in known_repos:
                if kr.lower() == consumer_norm:
                    matched_repo = kr
                    break

            if not matched_repo:
                continue

            # Check if consumer_repo's outbound deps mention this repo
            consumer_facts = all_facts[matched_repo]
            mentions_repo = False
            for dep in consumer_facts.outbound_deps:
                dep_name = re.split(r"[><=!~\s]", dep.get("dependency", ""))[0].strip().lower()
                dep_name = re.sub(r"^[a-zA-Z0-9_-]+/", "", dep_name)
                if dep_name == repo.lower() or dep_name == facts.package.name.lower():
                    mentions_repo = True
                    break

            if not mentions_repo:
                findings.append({
                    "category": "ghost-dependency",
                    "assumption": f"{repo} claims {matched_repo} depends on it",
                    "reality": f"{matched_repo}'s outbound deps don't mention {repo}",
                    "repos": sorted([repo, matched_repo]),
                    "confidence": "needs-verification",
                    "status": "active",
                    "source": facts.source_file,
                })

    return findings


def detect_deprecated_patterns(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find usage of known deprecated libraries/patterns."""
    findings = []

    for repo, facts in all_facts.items():
        # Search across all extractable text
        searchable = []
        for dep in facts.outbound_deps:
            searchable.append(dep.get("dependency", ""))
            searchable.append(dep.get("notes", ""))
        for cfg in facts.configs:
            searchable.append(cfg.get("config", ""))
            searchable.append(cfg.get("notes", ""))
        for api in facts.api_surface:
            searchable.append(api.get("endpoint", ""))
            searchable.append(api.get("notes", ""))
        for gap in facts.known_gaps:
            searchable.append(gap)

        combined = " ".join(searchable).lower()

        for dp in DEPRECATED_PATTERNS:
            if re.search(dp["pattern"], combined, re.IGNORECASE):
                findings.append({
                    "category": dp["category"],
                    "assumption": f"{repo} uses or references a deprecated pattern",
                    "reality": dp["reason"],
                    "repos": [repo],
                    "confidence": "high",
                    "status": "active",
                    "source": facts.source_file,
                })

    return findings


def detect_outdated_versions(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find version pins significantly behind the producer's current version."""
    producer_versions: dict[str, tuple[str, str]] = {}
    for repo, facts in all_facts.items():
        if facts.package.name and facts.package.version:
            producer_versions[facts.package.name.lower()] = (
                facts.package.version.lstrip("v"), repo
            )

    findings = []
    for repo, facts in all_facts.items():
        for dep in facts.outbound_deps:
            dep_str = dep.get("dependency", "")
            m = re.match(r"^([a-zA-Z0-9_-]+)\s*[><=!~]+\s*(.+)$", dep_str.strip())
            if not m:
                continue
            pkg_name = m.group(1).lower()
            pinned_ver = m.group(2).strip()

            if pkg_name not in producer_versions:
                continue

            prod_ver, prod_repo = producer_versions[pkg_name]
            if prod_repo == repo:
                continue

            # Compare major.minor segments
            try:
                pinned_parts = [int(x) for x in re.findall(r"\d+", pinned_ver)]
                prod_parts = [int(x) for x in re.findall(r"\d+", prod_ver)]
            except ValueError:
                continue

            if len(pinned_parts) < 2 or len(prod_parts) < 2:
                continue

            # Flag if more than 1 minor version behind
            if pinned_parts[0] == prod_parts[0] and prod_parts[1] - pinned_parts[1] > 1:
                findings.append({
                    "category": "outdated-version",
                    "assumption": f"{repo} pins {pkg_name}=={pinned_ver}",
                    "reality": f"Producer {prod_repo} is at version {prod_ver} "
                               f"({prod_parts[1] - pinned_parts[1]} minor versions ahead)",
                    "repos": sorted([repo, prod_repo]),
                    "confidence": "high",
                    "status": "active",
                    "source": facts.source_file,
                })

    return findings


def detect_orphan_secrets(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Find secrets that reference external repos/services not in any audit."""
    known_repos = {r.lower() for r in all_facts}
    findings = []

    for repo, facts in all_facts.items():
        for sec in facts.secrets:
            name = sec.get("name", "")
            usage = sec.get("usage", "")

            # Secrets referencing specific repos
            for m in re.finditer(r"([a-z][-a-z0-9_]*(?:/[a-z][-a-z0-9_]*))", usage.lower()):
                ref = m.group(1)
                parts = ref.split("/")
                ref_name = parts[-1] if len(parts) > 1 else parts[0]
                if ref_name not in known_repos and ref_name != repo.lower():
                    if len(ref_name) > 3 and ref_name not in ("github", "actions", "releases"):
                        findings.append({
                            "category": "dead-reference",
                            "assumption": f"{repo} has secret '{name}' used for '{usage}'",
                            "reality": f"References '{ref}' which has no audit",
                            "repos": [repo],
                            "confidence": "needs-verification",
                            "status": "active",
                            "source": facts.source_file,
                        })

    return findings


# ── Aggregation ──────────────────────────────────────────────────────────────


def _dedup_key(item: dict) -> str:
    return f"{item['category']}:{item['assumption']}"


def run_all_detectors(all_facts: dict[str, AuditFacts]) -> list[dict]:
    raw: list[dict] = []
    raw.extend(detect_dead_references(all_facts))
    raw.extend(detect_ghost_dependencies(all_facts))
    raw.extend(detect_deprecated_patterns(all_facts))
    raw.extend(detect_outdated_versions(all_facts))
    raw.extend(detect_orphan_secrets(all_facts))

    seen: set[str] = set()
    deduped = []
    for item in raw:
        key = _dedup_key(item)
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped


# ── Prose update ─────────────────────────────────────────────────────────────


def update_prose(items: list[dict]) -> None:
    """Update stale-assumptions.md with findings in the Moderate Risk section."""
    prose_path = config.MAPS_DIR / "stale-assumptions.md"
    text = prose_path.read_text()
    lines = text.splitlines()

    # Find the "Moderate Risk: Stale but Dormant" section and replace its table rows
    new_lines: list[str] = []
    in_moderate = False
    table_header_seen = False
    table_replaced = False

    for line in lines:
        if "## Moderate Risk: Stale but Dormant" in line:
            in_moderate = True
            new_lines.append(line)
            continue

        if in_moderate and line.strip().startswith("## "):
            in_moderate = False

        if in_moderate and line.strip().startswith("|") and "---" in line:
            table_header_seen = True
            new_lines.append(line)
            continue

        if in_moderate and table_header_seen and not table_replaced:
            # Replace all old rows with our new ones
            if line.strip().startswith("|"):
                continue  # skip old rows
            # We've reached the end of the table; insert our rows before this line
            for item in items:
                row = (
                    f"| {item['assumption']} "
                    f"| {item.get('reality', '')} "
                    f"| Verify "
                    f"| {item['confidence']} "
                    f"| {item['source']} |"
                )
                new_lines.append(row)
            table_replaced = True
            new_lines.append(line)
            continue

        new_lines.append(line)

    # Handle edge case: table is at the very end of the section
    if in_moderate and table_header_seen and not table_replaced:
        for item in items:
            row = (
                f"| {item['assumption']} "
                f"| {item.get('reality', '')} "
                f"| Verify "
                f"| {item['confidence']} "
                f"| {item['source']} |"
            )
            new_lines.append(row)

    text = "\n".join(new_lines)
    post = frontmatter.loads(text)
    post.metadata["freshness"] = "current"
    post.metadata["last_updated"] = date.today().isoformat()
    prose_path.write_text(frontmatter.dumps(post) + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────


def run(dry_run: bool = False) -> dict:
    all_facts = load_all_audits()
    findings = run_all_detectors(all_facts)

    data_path = config.MAPS_DATA_DIR / "stale-assumptions.json"
    if data_path.is_file():
        existing = json.loads(data_path.read_text())
    else:
        existing = {"schema_version": "1.0", "items": []}

    existing_items = existing.get("items", [])
    existing_assumptions = {i.get("assumption") for i in existing_items}

    new_items = []
    for f in findings:
        if f["assumption"] not in existing_assumptions:
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
    """Scan for stale assumptions across audit reports."""
    result = run(dry_run=dry_run)
    print(f"\nStale Assumption Scanner")
    print(f"{'=' * 40}")
    print(f"  Total findings: {result['total_findings']}")
    print(f"  New:            {result['new_findings']}")
    print(f"  Pre-existing:   {result['existing_findings']}")

    if result["items"]:
        print(f"\n  All stale assumptions:")
        for item in result["items"]:
            print(f"    {item['id']}: [{item['category']}] {item['assumption']}")
            print(f"          reality: {item.get('reality', 'unknown')}")
            print(f"          repos: {', '.join(item.get('repos', []))}")
    else:
        print(f"\n  WARNING: Zero stale assumptions found.")

    if dry_run:
        print(f"\n  (dry run — no files written)")


if __name__ == "__main__":
    main()
