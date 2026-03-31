#!/usr/bin/env python3
"""CLI tool for querying MCP's structured data files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import config

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
    """Load a data file by short name. Returns empty dict on missing/invalid."""
    path = config.MAPS_DATA_DIR / DATA_FILES[name]
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


# ── Output helpers ──────────────────────────────────────────────────────────


def _output(results: list[dict], as_json: bool) -> None:
    """Print results as JSON or a formatted table."""
    if as_json:
        click.echo(json.dumps(results, indent=2))
        return
    if not results:
        click.echo("No results.")
        return
    cols = list(results[0].keys())
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in results)) for c in cols}
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    click.echo(header)
    click.echo(sep)
    for row in results:
        line = " | ".join(str(row.get(c, "")).ljust(widths[c]) for c in cols)
        click.echo(line)


# ── CLI ─────────────────────────────────────────────────────────────────────


@click.group()
def cli():
    """Query MCP's structured knowledge data."""


@cli.command()
@click.option("--from", "from_repo", default=None, help="Filter by producer repo")
@click.option("--to", "to_repo", default=None, help="Filter by consumer repo")
@click.option("--type", "dep_type", default=None, help="Filter by dependency type")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def deps(from_repo: str | None, to_repo: str | None, dep_type: str | None, as_json: bool):
    """Query dependency edges."""
    data = _load("dependency-matrix")
    edges = data.get("edges", [])
    if from_repo:
        edges = [e for e in edges if e.get("from", "").lower() == from_repo.lower()]
    if to_repo:
        edges = [e for e in edges if e.get("to", "").lower() == to_repo.lower()]
    if dep_type:
        edges = [e for e in edges if e.get("type", "").lower() == dep_type.lower()]
    _output(edges, as_json)


@cli.command()
@click.option("--repo", default=None, help="Filter by repo name")
@click.option("--target", default=None, help="Filter by deployment target")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def deploy(repo: str | None, target: str | None, as_json: bool):
    """Query deployment pipelines."""
    data = _load("deployment-flow")
    pipelines = data.get("pipelines", [])
    if repo:
        pipelines = [p for p in pipelines if p.get("repo", "").lower() == repo.lower()]
    if target:
        t = target.lower()
        pipelines = [p for p in pipelines if t in [x.lower() for x in p.get("targets", [])]]
    _output(pipelines, as_json)


@cli.command()
@click.option("--status", default=None, help="Filter by status (open, resolved, etc.)")
@click.option("--impact", default=None, help="Filter by impact level (high, medium, low)")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def contradictions(status: str | None, impact: str | None, as_json: bool):
    """Query contradictions and ambiguities."""
    data = _load("contradictions")
    items = data.get("items", [])
    if status:
        items = [i for i in items if i.get("status", "").lower() == status.lower()]
    if impact:
        items = [i for i in items if i.get("impact", "").lower() == impact.lower()]
    _output(items, as_json)


@cli.command()
@click.option("--status", default=None, help="Filter by status (confirmed-stale, etc.)")
@click.option("--repo", default=None, help="Filter by affected repo")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def stale(status: str | None, repo: str | None, as_json: bool):
    """Query stale assumptions."""
    data = _load("stale-assumptions")
    items = data.get("items", [])
    if status:
        items = [i for i in items if i.get("status", "").lower() == status.lower()]
    if repo:
        r = repo.lower()
        items = [i for i in items if r in [x.lower() for x in i.get("repos_affected", [])]]
    _output(items, as_json)


@cli.command()
@click.option("--tier", default=None, help="Filter by effort tier (quick-win, medium, etc.)")
@click.option("--status", default=None, help="Filter by status (proposed, approved, etc.)")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def simplify(tier: str | None, status: str | None, as_json: bool):
    """Query candidate simplifications."""
    data = _load("simplifications")
    candidates = data.get("candidates", [])
    if tier:
        candidates = [c for c in candidates if c.get("tier", "").lower() == tier.lower()]
    if status:
        candidates = [c for c in candidates if c.get("status", "").lower() == status.lower()]
    _output(candidates, as_json)


@cli.command("docs")
@click.option("--severity", default=None, help="Filter by severity (critical, moderate, minor)")
@click.option("--repo", default=None, help="Filter by repo")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def docs_cmd(severity: str | None, repo: str | None, as_json: bool):
    """Query missing documentation items."""
    data = _load("missing-docs")
    items = data.get("items", [])
    if severity:
        items = [i for i in items if i.get("severity", "").lower() == severity.lower()]
    if repo:
        r = repo.lower()
        items = [i for i in items if r in i.get("repo", "").lower()]
    _output(items, as_json)


@cli.command()
@click.option("--repo", required=True, help="Repo name to analyze")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def impact(repo: str, as_json: bool):
    """Cross-cutting impact query: show everything involving a repo."""
    r = repo.lower()
    result: dict = {"repo": repo}

    # Dependencies (as producer or consumer)
    dep_data = _load("dependency-matrix")
    edges = dep_data.get("edges", [])
    result["produces_for"] = [
        e for e in edges if e.get("from", "").lower() == r
    ]
    result["consumes_from"] = [
        e for e in edges if e.get("to", "").lower() == r
    ]

    # Deployment
    deploy_data = _load("deployment-flow")
    result["deployment"] = [
        p for p in deploy_data.get("pipelines", [])
        if p.get("repo", "").lower() == r
    ]

    # Contradictions
    contra_data = _load("contradictions")
    result["contradictions"] = [
        i for i in contra_data.get("items", [])
        if r in [s.lower() for s in i.get("sources", [])]
        or r in i.get("summary", "").lower()
    ]

    # Stale assumptions
    stale_data = _load("stale-assumptions")
    result["stale_assumptions"] = [
        i for i in stale_data.get("items", [])
        if r in [x.lower() for x in i.get("repos_affected", [])]
    ]

    # Simplifications
    simp_data = _load("simplifications")
    result["simplifications"] = [
        c for c in simp_data.get("candidates", [])
        if r in [x.lower() for x in c.get("repos", [])]
    ]

    # Missing docs
    docs_data = _load("missing-docs")
    result["missing_docs"] = [
        i for i in docs_data.get("items", [])
        if r in i.get("repo", "").lower()
    ]

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    click.echo(f"=== Impact Report: {repo} ===\n")

    if result["produces_for"]:
        click.echo(f"Produces for ({len(result['produces_for'])} edges):")
        for e in result["produces_for"]:
            click.echo(f"  -> {e['to']} ({e.get('type', '?')})")
    else:
        click.echo("Produces for: none")

    if result["consumes_from"]:
        click.echo(f"\nConsumes from ({len(result['consumes_from'])} edges):")
        for e in result["consumes_from"]:
            click.echo(f"  <- {e['from']} ({e.get('type', '?')})")
    else:
        click.echo("\nConsumes from: none")

    if result["deployment"]:
        click.echo(f"\nDeployment ({len(result['deployment'])} pipelines):")
        for p in result["deployment"]:
            targets = ", ".join(p.get("targets", []))
            click.echo(f"  {p.get('ci', '?')} -> {p.get('cd', '?')} -> {targets}")
    else:
        click.echo("\nDeployment: none found")

    for section, label in [
        ("contradictions", "Contradictions"),
        ("stale_assumptions", "Stale Assumptions"),
        ("simplifications", "Simplifications"),
        ("missing_docs", "Missing Docs"),
    ]:
        items = result[section]
        if items:
            click.echo(f"\n{label} ({len(items)}):")
            for i in items:
                summary = i.get("summary") or i.get("title") or i.get("description", "?")
                click.echo(f"  - {summary}")
        else:
            click.echo(f"\n{label}: none")

    click.echo()


if __name__ == "__main__":
    cli()
