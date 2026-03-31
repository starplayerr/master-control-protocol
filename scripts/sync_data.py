#!/usr/bin/env python3
"""Sync checker between prose maps and structured data files.

Detects when the prose maps and their JSON data companions drift apart.
"""

from __future__ import annotations

import json
import sys
from difflib import unified_diff
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import config

# ── Map ↔ Data file pairing ────────────────────────────────────────────────

MAP_PAIRS: list[dict] = [
    {
        "name": "dependency-matrix",
        "prose": config.MAPS_DIR / "dependency-matrix.md",
        "data": config.MAPS_DATA_DIR / "dependency-matrix.json",
        "data_key": "edges",
        "prose_tables": [
            {"section": "Library / Package Flows", "id_col": "Producer"},
            {"section": "Container Image Flows", "id_col": "Producer"},
            {"section": "Infrastructure Flows", "id_col": "Producer"},
            {"section": "Dependency Matrix Table", "id_col": "Producer"},
            {"section": "Unexpected or Concerning Dependencies", "id_col": "Dependency"},
        ],
    },
    {
        "name": "deployment-flow",
        "prose": config.MAPS_DIR / "deployment-flow.md",
        "data": config.MAPS_DATA_DIR / "deployment-flow.json",
        "data_key": "pipelines",
        "prose_tables": [
            {"section": "Deployment Paths by Repo", "id_col": "Repo"},
        ],
    },
    {
        "name": "source-of-truth",
        "prose": config.MAPS_DIR / "source-of-truth.md",
        "data": config.MAPS_DATA_DIR / "source-of-truth.json",
        "data_key": "config_keys",
        "prose_tables": [
            {"section": "Source of Truth Registry", "id_col": "Dimension"},
        ],
    },
    {
        "name": "contradictions-and-ambiguities",
        "prose": config.MAPS_DIR / "contradictions-and-ambiguities.md",
        "data": config.MAPS_DATA_DIR / "contradictions-and-ambiguities.json",
        "data_key": "items",
        "prose_tables": [
            {"section": "Active Contradictions", "id_col": "ID"},
            {"section": "Ambiguities", "id_col": "ID"},
            {"section": "Not-Yet Contradictions", "id_col": "ID"},
        ],
    },
    {
        "name": "stale-assumptions",
        "prose": config.MAPS_DIR / "stale-assumptions.md",
        "data": config.MAPS_DATA_DIR / "stale-assumptions.json",
        "data_key": "items",
        "prose_tables": [
            {"section": "High Risk: Deployed but Unwanted", "id_col": "Item"},
            {"section": "Medium Risk: Should Be Deleted", "id_col": "Repo"},
            {"section": "Moderate Risk: Stale but Dormant", "id_col": "Assumption"},
            {"section": "Low Risk: Housekeeping", "id_col": "Repo"},
        ],
    },
    {
        "name": "candidate-simplifications",
        "prose": config.MAPS_DIR / "candidate-simplifications.md",
        "data": config.MAPS_DATA_DIR / "candidate-simplifications.json",
        "data_key": "candidates",
        "prose_tables": [
            {"section": "Catalog", "id_col": "ID"},
        ],
    },
    {
        "name": "missing-docs",
        "prose": config.MAPS_DIR / "missing-docs.md",
        "data": config.MAPS_DATA_DIR / "missing-docs.json",
        "data_key": "items",
        "prose_tables": [
            {"section": "Critical Gaps", "id_col": "ID"},
            {"section": "Moderate Gaps", "id_col": "ID"},
            {"section": "Minor Gaps / Nice-to-Have", "id_col": "ID"},
        ],
    },
]


# ── Markdown table parser ───────────────────────────────────────────────────


def _is_real_row(row: dict) -> bool:
    """Return True if a table row contains actual data, not just template hints.

    Filters out rows that are only placeholders/option lists like
    'high · medium · low' or 'not started · in progress · verified',
    and rows that only have a single non-empty cell (template scaffolding).
    """
    real_cells = 0
    for v in row.values():
        v = v.strip().strip("_")
        if not v or v == "—":
            continue
        if " · " in v:
            continue
        real_cells += 1
    return real_cells >= 2


def _parse_md_tables(path: Path) -> list[dict]:
    """Parse all markdown tables from a file.

    Returns a list of dicts, each with 'section' (nearest heading),
    'columns' (list of column names), and 'rows' (list of dicts).
    """
    if not path.is_file():
        return []

    lines = path.read_text().splitlines()
    tables: list[dict] = []
    current_section = ""

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#"):
            current_section = line.lstrip("#").strip()
            i += 1
            continue

        if line.startswith("|") and "---" not in line:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if not cols:
                i += 1
                continue

            # Next line should be the separator
            if i + 1 < len(lines) and "---" in lines[i + 1]:
                i += 2  # skip header + separator
            else:
                i += 1
                continue

            rows: list[dict] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].split("|")[1:-1]]
                if len(cells) >= len(cols):
                    row = {cols[j]: cells[j] for j in range(len(cols))}
                    if _is_real_row(row):
                        rows.append(row)
                i += 1

            tables.append({
                "section": current_section,
                "columns": cols,
                "rows": rows,
            })
            continue

        i += 1

    return tables


def _count_prose_rows(pair: dict) -> int:
    """Count non-empty rows across all relevant tables in a prose map."""
    tables = _parse_md_tables(pair["prose"])
    total = 0
    target_sections = {t["section"] for t in pair["prose_tables"]}
    for table in tables:
        if table["section"] in target_sections:
            total += len(table["rows"])
    return total


def _count_data_entries(pair: dict) -> int:
    """Count entries in a data file."""
    if not pair["data"].is_file():
        return 0
    try:
        data = json.loads(pair["data"].read_text())
        return len(data.get(pair["data_key"], []))
    except (json.JSONDecodeError, OSError):
        return 0


# ── Check mode ──────────────────────────────────────────────────────────────


def check_sync() -> list[dict]:
    """Compare prose maps with data files and return findings."""
    findings: list[dict] = []

    for pair in MAP_PAIRS:
        prose_exists = pair["prose"].is_file()
        data_exists = pair["data"].is_file()
        prose_count = _count_prose_rows(pair) if prose_exists else 0
        data_count = _count_data_entries(pair) if data_exists else 0

        status = "ok"
        detail = ""

        if not prose_exists:
            status = "error"
            detail = "prose map missing"
        elif not data_exists:
            status = "error"
            detail = "data file missing"
        elif prose_count == 0 and data_count == 0:
            status = "empty"
            detail = "both prose and data are empty"
        elif prose_count > 0 and data_count == 0:
            status = "drift"
            detail = f"prose has {prose_count} entries, data file is empty"
        elif prose_count == 0 and data_count > 0:
            status = "drift"
            detail = f"data has {data_count} entries, prose tables are empty"
        elif prose_count != data_count:
            status = "drift"
            detail = f"count mismatch: {prose_count} in prose, {data_count} in data"
        else:
            detail = f"{data_count} entries in sync"

        findings.append({
            "map": pair["name"],
            "prose": str(pair["prose"].relative_to(config.MCP_ROOT)),
            "data": str(pair["data"].relative_to(config.MCP_ROOT)),
            "prose_rows": prose_count,
            "data_entries": data_count,
            "status": status,
            "detail": detail,
        })

    return findings


def print_check_report(findings: list[dict]) -> None:
    """Print a human-readable sync report."""
    click.echo("=" * 60)
    click.echo("MCP PROSE ↔ DATA SYNC REPORT")
    click.echo("=" * 60)
    click.echo()

    drifted = [f for f in findings if f["status"] == "drift"]
    errors = [f for f in findings if f["status"] == "error"]
    empty = [f for f in findings if f["status"] == "empty"]
    ok = [f for f in findings if f["status"] == "ok"]

    if errors:
        click.echo(f"ERRORS ({len(errors)}):")
        for f in errors:
            click.echo(f"  ✗ {f['map']}: {f['detail']}")
        click.echo()

    if drifted:
        click.echo(f"DRIFT ({len(drifted)}):")
        for f in drifted:
            click.echo(f"  ! {f['map']}: {f['detail']}")
        click.echo()

    if empty:
        click.echo(f"EMPTY ({len(empty)}):")
        for f in empty:
            click.echo(f"  ~ {f['map']}")
        click.echo()

    if ok:
        click.echo(f"IN SYNC ({len(ok)}):")
        for f in ok:
            click.echo(f"  . {f['map']}: {f['detail']}")
        click.echo()

    click.echo("-" * 60)
    click.echo(
        f"Total: {len(findings)} maps | "
        f"{len(ok)} synced | "
        f"{len(drifted)} drifted | "
        f"{len(empty)} empty | "
        f"{len(errors)} errors"
    )


# ── From-prose mode ─────────────────────────────────────────────────────────


def _prose_to_dep_edges(pair: dict) -> list[dict]:
    """Extract dependency edges from prose dependency-matrix tables."""
    tables = _parse_md_tables(pair["prose"])
    edges: list[dict] = []

    for table in tables:
        if table["section"] == "Dependency Matrix Table":
            for row in table["rows"]:
                edges.append({
                    "from": row.get("Producer", ""),
                    "to": row.get("Consumer", ""),
                    "type": row.get("Link Type", ""),
                    "direction": "consumed-by",
                    "confidence": "verified",
                    "source_audit": row.get("Source", ""),
                    "notes": row.get("Notes", ""),
                })
        elif table["section"] in ("Library / Package Flows",):
            for row in table["rows"]:
                edges.append({
                    "from": row.get("Producer", ""),
                    "to": row.get("Consumer(s)", ""),
                    "type": "library",
                    "direction": "consumed-by",
                    "confidence": "verified",
                    "source_audit": row.get("Source", ""),
                    "notes": row.get("Notes", ""),
                })

    return edges


def _prose_to_pipelines(pair: dict) -> list[dict]:
    """Extract deployment pipelines from prose deployment-flow tables."""
    tables = _parse_md_tables(pair["prose"])
    pipelines: list[dict] = []

    for table in tables:
        if table["section"] == "Deployment Paths by Repo":
            for row in table["rows"]:
                pipelines.append({
                    "repo": row.get("Repo", ""),
                    "trigger": "unknown",
                    "ci": row.get("CI System", "").lower().replace(" ", "-"),
                    "cd": row.get("CD System", "").lower().replace(" ", "-"),
                    "targets": [row.get("Target", "")],
                    "pipeline_files": [f.strip() for f in row.get("Pipeline File(s)", "").split(",") if f.strip()],
                    "rollback": "unknown",
                    "confidence": "verified",
                    "source_audit": row.get("Source", ""),
                })

    return pipelines


def _prose_to_items(pair: dict) -> list[dict]:
    """Generic: extract items from prose tables with an ID column."""
    tables = _parse_md_tables(pair["prose"])
    items: list[dict] = []
    target_sections = {t["section"] for t in pair["prose_tables"]}

    for table in tables:
        if table["section"] in target_sections:
            for row in table["rows"]:
                items.append(row)

    return items


PROSE_EXTRACTORS = {
    "dependency-matrix": _prose_to_dep_edges,
    "deployment-flow": _prose_to_pipelines,
    "source-of-truth": _prose_to_items,
    "contradictions-and-ambiguities": _prose_to_items,
    "stale-assumptions": _prose_to_items,
    "candidate-simplifications": _prose_to_items,
    "missing-docs": _prose_to_items,
}


def from_prose(confirm: bool) -> None:
    """Extract structured data from prose maps and update data files."""
    for pair in MAP_PAIRS:
        name = pair["name"]
        extractor = PROSE_EXTRACTORS.get(name, _prose_to_items)
        new_entries = extractor(pair)

        if not new_entries:
            click.echo(f"  {name}: no data in prose, skipping")
            continue

        data_path = pair["data"]
        data_key = pair["data_key"]

        if data_path.is_file():
            old_data = json.loads(data_path.read_text())
        else:
            old_data = {"schema_version": "1.0"}

        old_entries = old_data.get(data_key, [])
        new_data = dict(old_data)
        new_data[data_key] = new_entries

        old_text = json.dumps(old_data, indent=2) + "\n"
        new_text = json.dumps(new_data, indent=2) + "\n"

        if old_text == new_text:
            click.echo(f"  {name}: already in sync ({len(new_entries)} entries)")
            continue

        click.echo(f"\n  {name}: {len(old_entries)} -> {len(new_entries)} entries")

        diff = list(unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{data_path.name}",
            tofile=f"b/{data_path.name}",
        ))

        if diff:
            for line in diff[:50]:
                click.echo(f"    {line}", nl=False)
            if len(diff) > 50:
                click.echo(f"    ... ({len(diff) - 50} more diff lines)")

        if confirm:
            data_path.parent.mkdir(parents=True, exist_ok=True)
            data_path.write_text(new_text)
            click.echo(f"  -> Updated {data_path.relative_to(config.MCP_ROOT)}")
        else:
            click.echo(f"  (dry run — use --yes to write)")


# ── CLI ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--check", "mode_check", is_flag=True, help="Check sync status between prose and data files")
@click.option("--from-prose", "mode_from_prose", is_flag=True, help="Update data files from prose map tables")
@click.option("--yes", "confirm", is_flag=True, help="Actually write changes (default is dry run)")
@click.option("--json", "as_json", is_flag=True, help="Output check results as JSON")
def main(mode_check: bool, mode_from_prose: bool, confirm: bool, as_json: bool) -> None:
    """Sync checker between MCP prose maps and structured data files."""
    if not mode_check and not mode_from_prose:
        mode_check = True

    if mode_check:
        findings = check_sync()
        if as_json:
            click.echo(json.dumps(findings, indent=2))
        else:
            print_check_report(findings)

        drifted = sum(1 for f in findings if f["status"] in ("drift", "error"))
        sys.exit(1 if drifted else 0)

    if mode_from_prose:
        click.echo("Extracting structured data from prose maps...\n")
        from_prose(confirm)
        click.echo("\nDone.")


if __name__ == "__main__":
    main()
