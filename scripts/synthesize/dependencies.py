#!/usr/bin/env python3
"""Dependency graph builder.

Reads extracted audit facts and builds the cross-repo dependency matrix,
detects cycles, identifies single points of failure, and generates a
Mermaid diagram.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from synthesize.extract import AuditFacts, load_all_audits


# ── Edge extraction ──────────────────────────────────────────────────────────

# Normalise repo names for matching: lowercase, strip org prefixes, collapse
# whitespace.  E.g. "astral-sh/ruff" -> "ruff"
_ORG_PREFIX = re.compile(r"^[a-zA-Z0-9_-]+/")


def _norm(name: str) -> str:
    name = name.strip().lower()
    name = _ORG_PREFIX.sub("", name)
    return name


def _classify_dep_type(dep_str: str, type_str: str, notes: str) -> str:
    """Map audit dependency type strings to edge types."""
    combined = f"{type_str} {notes}".lower()
    if "container" in combined or "docker" in combined or "image" in combined:
        return "container-image"
    if "api" in combined or "endpoint" in combined:
        return "api-call"
    if "config" in combined:
        return "shared-config"
    if "infra" in combined or "terraform" in combined:
        return "infra-dependency"
    if "data" in combined or "s3" in combined or "kafka" in combined:
        return "data-flow"
    if "build" in combined:
        return "build-tool"
    return "library"


def extract_edges(all_facts: dict[str, AuditFacts]) -> list[dict]:
    """Derive dependency edges by cross-referencing audit facts."""
    known_repos = set(all_facts.keys())
    known_norm = {_norm(r): r for r in known_repos}

    # Also build package-name -> repo mapping from package details + artifacts
    pkg_to_repo: dict[str, str] = {}
    for repo, facts in all_facts.items():
        if facts.package.name:
            pkg_to_repo[_norm(facts.package.name)] = repo
        for art in facts.artifacts:
            aname = _norm(art.get("name", ""))
            if aname:
                pkg_to_repo[aname] = repo

    edges: list[dict] = []
    seen: set[tuple] = set()

    for repo, facts in all_facts.items():
        # --- Outbound deps that match known repos/packages ---
        for dep in facts.outbound_deps:
            dep_name_raw = dep.get("dependency", "")
            dep_type = dep.get("type", "")
            notes = dep.get("notes", "")

            # Extract package name (strip version pins like ==0.15.8)
            dep_name_clean = re.split(r"[><=!~\s]", dep_name_raw)[0].strip()
            dep_norm = _norm(dep_name_clean)

            target_repo = known_norm.get(dep_norm) or pkg_to_repo.get(dep_norm)
            if target_repo and target_repo != repo:
                key = (target_repo, repo, _classify_dep_type(dep_name_raw, dep_type, notes))
                if key not in seen:
                    seen.add(key)
                    edges.append({
                        "from": target_repo,
                        "to": repo,
                        "type": key[2],
                        "direction": "consumed-by",
                        "confidence": "verified",
                        "source_audit": facts.source_file,
                        "notes": f"{repo} depends on {dep_name_raw}" + (f" ({notes})" if notes else ""),
                    })

        # --- Inbound consumers that match known repos ---
        for inb in facts.inbound_deps:
            consumer_raw = inb.get("consumer", "")
            consumer_norm = _norm(consumer_raw)
            consumer_type = inb.get("type", "")
            notes = inb.get("notes", "")

            target_repo = known_norm.get(consumer_norm)
            # Try partial match: "astral-sh/uv users" -> look for "uv"
            if not target_repo:
                for known_n, known_r in known_norm.items():
                    if known_n in consumer_norm.split() or consumer_norm.startswith(known_n):
                        target_repo = known_r
                        break
            if target_repo and target_repo != repo:
                etype = _classify_dep_type(consumer_raw, consumer_type, notes)
                key = (repo, target_repo, etype)
                if key not in seen:
                    seen.add(key)
                    edges.append({
                        "from": repo,
                        "to": target_repo,
                        "type": etype,
                        "direction": "consumed-by",
                        "confidence": "verified",
                        "source_audit": facts.source_file,
                        "notes": f"{target_repo} consumes {repo}" + (f" ({notes})" if notes else ""),
                    })

    return edges


# ── Cycle detection ──────────────────────────────────────────────────────────


def detect_cycles(edges: list[dict]) -> list[list[str]]:
    """Find cycles in the dependency graph via DFS."""
    graph: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        graph[e["from"]].append(e["to"])

    visited: set[str] = set()
    on_stack: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str, path: list[str]) -> None:
        visited.add(node)
        on_stack.add(node)
        path.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path)
            elif neighbor in on_stack:
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
        path.pop()
        on_stack.discard(node)

    all_nodes = set(graph.keys())
    for e in edges:
        all_nodes.add(e["to"])

    for node in all_nodes:
        if node not in visited:
            dfs(node, [])

    return cycles


# ── Risk analysis ────────────────────────────────────────────────────────────


def compute_risk(edges: list[dict]) -> list[dict]:
    """Identify high-risk nodes: many dependents, potential SPOF."""
    in_degree: dict[str, set[str]] = defaultdict(set)
    out_degree: dict[str, set[str]] = defaultdict(set)

    for e in edges:
        in_degree[e["to"]].add(e["from"])
        out_degree[e["from"]].add(e["to"])

    risks = []
    for node, dependents in sorted(in_degree.items(), key=lambda x: -len(x[1])):
        if len(dependents) >= 2:
            risks.append({
                "repo": node,
                "dependent_count": len(dependents),
                "dependents": sorted(dependents),
                "risk": "high" if len(dependents) >= 3 else "medium",
            })
    return risks


# ── Mermaid diagram ──────────────────────────────────────────────────────────


def generate_mermaid(edges: list[dict], cycles: list[list[str]], risks: list[dict]) -> str:
    """Build a Mermaid flowchart from the dependency edges."""
    lines = [
        "---",
        'title: "Dependency Matrix"',
        "role: diagram",
        f"last_updated: {date.today().isoformat()}",
        "depends_on:",
        "  - maps/data/dependency-matrix.json",
        "freshness: current",
        "scope: platform",
        "---",
        "",
        "# Dependency Matrix Diagram",
        "",
        "```mermaid",
        "flowchart TD",
    ]

    risk_repos = {r["repo"] for r in risks if r["risk"] == "high"}

    all_nodes: set[str] = set()
    for e in edges:
        all_nodes.add(e["from"])
        all_nodes.add(e["to"])

    # Sanitise node names for mermaid
    def node_id(name: str) -> str:
        return name.replace("-", "_").replace(".", "_")

    for node in sorted(all_nodes):
        nid = node_id(node)
        if node in risk_repos:
            lines.append(f'    {nid}["{node} (SPOF)"]')
        else:
            lines.append(f'    {nid}["{node}"]')

    for e in edges:
        src = node_id(e["from"])
        tgt = node_id(e["to"])
        etype = e["type"]
        lines.append(f'    {src} -->|"{etype}"| {tgt}')

    lines.append("```")

    if cycles:
        lines.append("")
        lines.append("## Detected Cycles")
        lines.append("")
        for c in cycles:
            lines.append(f"- {' -> '.join(c)}")

    if risks:
        lines.append("")
        lines.append("## High-Risk Nodes")
        lines.append("")
        lines.append("| Repo | Dependents | Risk |")
        lines.append("|---|---|---|")
        for r in risks:
            lines.append(f"| {r['repo']} | {', '.join(r['dependents'])} | {r['risk']} |")

    return "\n".join(lines) + "\n"


# ── JSON merge ───────────────────────────────────────────────────────────────


def merge_edges(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge new edges into existing, preserving manually-added ones."""
    def edge_key(e: dict) -> tuple:
        return (e.get("from", ""), e.get("to", ""), e.get("type", ""))

    existing_keys = {edge_key(e) for e in existing}
    new_keys = {edge_key(e) for e in new}

    merged = list(new)
    for e in existing:
        if edge_key(e) not in new_keys:
            merged.append(e)

    return merged


# ── Main ─────────────────────────────────────────────────────────────────────


def run(dry_run: bool = False) -> dict:
    """Run the dependency graph builder. Returns summary stats."""
    all_facts = load_all_audits()
    new_edges = extract_edges(all_facts)
    cycles = detect_cycles(new_edges)
    risks = compute_risk(new_edges)

    # Load existing data
    data_path = config.MAPS_DATA_DIR / "dependency-matrix.json"
    if data_path.is_file():
        existing = json.loads(data_path.read_text())
    else:
        existing = {"schema_version": "1.0", "edges": []}

    old_edges = existing.get("edges", [])
    merged = merge_edges(old_edges, new_edges)

    if not dry_run:
        existing["edges"] = merged
        data_path.write_text(json.dumps(existing, indent=2) + "\n")

        diagram = generate_mermaid(merged, cycles, risks)
        diagram_path = config.DIAGRAMS_DIR / "dependency-matrix.md"
        diagram_path.parent.mkdir(parents=True, exist_ok=True)
        diagram_path.write_text(diagram)

    return {
        "edges_discovered": len(new_edges),
        "edges_existing": len(old_edges),
        "edges_merged": len(merged),
        "cycles": cycles,
        "high_risk_nodes": risks,
    }


@click.command()
@click.option("--dry-run", is_flag=True, help="Don't write changes")
def main(dry_run: bool) -> None:
    """Build the cross-repo dependency graph from audit reports."""
    result = run(dry_run=dry_run)
    print(f"\nDependency Graph Builder")
    print(f"{'=' * 40}")
    print(f"  Edges discovered: {result['edges_discovered']}")
    print(f"  Edges in existing data: {result['edges_existing']}")
    print(f"  Edges after merge: {result['edges_merged']}")

    if result["cycles"]:
        print(f"\n  Cycles detected: {len(result['cycles'])}")
        for c in result["cycles"]:
            print(f"    {' -> '.join(c)}")
    else:
        print(f"\n  No cycles detected")

    if result["high_risk_nodes"]:
        print(f"\n  High-risk nodes:")
        for r in result["high_risk_nodes"]:
            print(f"    {r['repo']}: {r['dependent_count']} dependents ({r['risk']})")

    if dry_run:
        print(f"\n  (dry run — no files written)")


if __name__ == "__main__":
    main()
