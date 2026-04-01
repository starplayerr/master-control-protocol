#!/usr/bin/env python3
"""MCP server exposing Master Control Protocol's queryable knowledge layer.

Run with:
    python scripts/mcp_server.py          # stdio transport (for Cursor / Claude Code)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP

from lib import config
from lib.inventory import COLUMNS

mcp = FastMCP(
    "master-control-protocol",
    instructions=(
        "Query the Master Control Protocol knowledge base. "
        "Use these tools to find dependencies, deployment flows, "
        "contradictions, stale assumptions, simplification candidates, "
        "documentation gaps, and cross-cutting impact for any repo."
    ),
)

# ── Data loading ────────────────────────────────────────────────────────────

DATA_FILES = {
    "dependency-matrix": "dependency-matrix.json",
    "deployment-flow": "deployment-flow.json",
    "source-of-truth": "source-of-truth.json",
    "contradictions": "contradictions-and-ambiguities.json",
    "stale-assumptions": "stale-assumptions.json",
    "simplifications": "candidate-simplifications.json",
    "missing-docs": "missing-docs.json",
}


def _load(name: str) -> dict:
    path = config.MAPS_DATA_DIR / DATA_FILES[name]
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


# ── Tools ───────────────────────────────────────────────────────────────────


@mcp.tool()
def query_dependencies(
    repo: str | None = None,
    dep_type: str | None = None,
    direction: str | None = None,
) -> str:
    """Find dependency edges between repos.

    Args:
        repo: Filter by repo name (matches both 'from' and 'to' fields).
        dep_type: Filter by dependency type (library, build-tool, etc.).
        direction: Filter by direction (consumed-by, etc.).
    """
    data = _load("dependency-matrix")
    edges = data.get("edges", [])
    if repo:
        r = repo.lower()
        edges = [e for e in edges if e.get("from", "").lower() == r or e.get("to", "").lower() == r]
    if dep_type:
        edges = [e for e in edges if e.get("type", "").lower() == dep_type.lower()]
    if direction:
        edges = [e for e in edges if e.get("direction", "").lower() == direction.lower()]
    return json.dumps(edges, indent=2)


@mcp.tool()
def query_deployments(
    repo: str | None = None,
    target: str | None = None,
) -> str:
    """Find deployment pipelines for repos.

    Args:
        repo: Filter by repo name.
        target: Filter by deployment target (pypi, github-releases, eks-prod, etc.).
    """
    data = _load("deployment-flow")
    pipelines = data.get("pipelines", [])
    if repo:
        pipelines = [p for p in pipelines if p.get("repo", "").lower() == repo.lower()]
    if target:
        t = target.lower()
        pipelines = [p for p in pipelines if t in [x.lower() for x in p.get("targets", [])]]
    return json.dumps(pipelines, indent=2)


@mcp.tool()
def query_contradictions(
    status: str | None = None,
    impact: str | None = None,
) -> str:
    """Find contradictions and ambiguities across the platform.

    Args:
        status: Filter by status (open, resolved, etc.).
        impact: Filter by impact level (high, medium, low).
    """
    data = _load("contradictions")
    items = data.get("items", [])
    if status:
        items = [i for i in items if i.get("status", "").lower() == status.lower()]
    if impact:
        items = [i for i in items if i.get("impact", "").lower() == impact.lower()]
    return json.dumps(items, indent=2)


@mcp.tool()
def query_stale_assumptions(
    status: str | None = None,
    repo: str | None = None,
) -> str:
    """Find stale assumptions that may no longer hold.

    Args:
        status: Filter by status (confirmed-stale, etc.).
        repo: Filter by affected repo name.
    """
    data = _load("stale-assumptions")
    items = data.get("items", [])
    if status:
        items = [i for i in items if i.get("status", "").lower() == status.lower()]
    if repo:
        r = repo.lower()
        items = [i for i in items if r in [x.lower() for x in i.get("repos_affected", [])]]
    return json.dumps(items, indent=2)


@mcp.tool()
def query_simplifications(
    tier: str | None = None,
    status: str | None = None,
) -> str:
    """Find candidate simplifications to reduce platform complexity.

    Args:
        tier: Filter by effort tier (quick-win, medium, significant).
        status: Filter by status (proposed, approved, in-progress, done).
    """
    data = _load("simplifications")
    candidates = data.get("candidates", [])
    if tier:
        candidates = [c for c in candidates if c.get("tier", "").lower() == tier.lower()]
    if status:
        candidates = [c for c in candidates if c.get("status", "").lower() == status.lower()]
    return json.dumps(candidates, indent=2)


@mcp.tool()
def query_missing_docs(
    severity: str | None = None,
    repo: str | None = None,
) -> str:
    """Find documentation gaps across the ecosystem.

    Args:
        severity: Filter by severity (critical, moderate, minor).
        repo: Filter by repo name.
    """
    data = _load("missing-docs")
    items = data.get("items", [])
    if severity:
        items = [i for i in items if i.get("severity", "").lower() == severity.lower()]
    if repo:
        r = repo.lower()
        items = [i for i in items if r in i.get("repo", "").lower()]
    return json.dumps(items, indent=2)


@mcp.tool()
def query_repo_impact(repo: str) -> str:
    """Cross-cutting impact analysis: show everything involving a given repo.

    Returns dependencies (in/out), deployment pipelines, contradictions,
    stale assumptions, simplification candidates, and missing docs.

    Args:
        repo: The repo name to analyze.
    """
    r = repo.lower()
    result: dict = {"repo": repo}

    dep_data = _load("dependency-matrix")
    edges = dep_data.get("edges", [])
    result["produces_for"] = [e for e in edges if e.get("from", "").lower() == r]
    result["consumes_from"] = [e for e in edges if e.get("to", "").lower() == r]

    deploy_data = _load("deployment-flow")
    result["deployment"] = [
        p for p in deploy_data.get("pipelines", []) if p.get("repo", "").lower() == r
    ]

    contra_data = _load("contradictions")
    result["contradictions"] = [
        i for i in contra_data.get("items", [])
        if r in [s.lower() for s in i.get("sources", [])] or r in i.get("summary", "").lower()
    ]

    stale_data = _load("stale-assumptions")
    result["stale_assumptions"] = [
        i for i in stale_data.get("items", []) if r in [x.lower() for x in i.get("repos_affected", [])]
    ]

    simp_data = _load("simplifications")
    result["simplifications"] = [
        c for c in simp_data.get("candidates", []) if r in [x.lower() for x in c.get("repos", [])]
    ]

    docs_data = _load("missing-docs")
    result["missing_docs"] = [
        i for i in docs_data.get("items", []) if r in i.get("repo", "").lower()
    ]

    return json.dumps(result, indent=2)


@mcp.tool()
def get_inventory() -> str:
    """Return the full repository inventory as structured JSON.

    Parses INVENTORY.md and returns all repos with their metadata:
    name, surface, purpose, owner, tech stack, prod status, and audit status.
    """
    path = config.INVENTORY_PATH
    if not path.is_file():
        return json.dumps({"error": "INVENTORY.md not found"})

    content = path.read_text()
    lines = content.splitlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| Repo") and "Surface" in line:
            header_idx = i
            break

    if header_idx is None:
        return json.dumps({"error": "Could not parse inventory table"})

    data_start = header_idx + 2
    rows: list[dict] = []
    for i in range(data_start, len(lines)):
        line = lines[i].strip()
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= len(COLUMNS):
            row = {COLUMNS[j]: cells[j] for j in range(len(COLUMNS))}
            rows.append(row)

    return json.dumps({"repos": rows, "total": len(rows)}, indent=2)


@mcp.tool()
def get_freshness_report() -> str:
    """Return the staleness status of all MCP markdown files.

    Reports which files are current, stale, draft, or unknown,
    including which dependencies triggered staleness.
    """
    from check_freshness import check_freshness_all

    findings = check_freshness_all()
    summary = {
        "total": len(findings),
        "current": sum(1 for f in findings if f["computed_freshness"] == "current"),
        "stale": sum(1 for f in findings if f["computed_freshness"] == "stale"),
        "draft": sum(1 for f in findings if f["computed_freshness"] == "draft"),
        "unknown": sum(1 for f in findings if f["computed_freshness"] == "unknown"),
        "files": findings,
    }
    return json.dumps(summary, indent=2)


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
