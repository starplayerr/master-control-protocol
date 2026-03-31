"""Shared Markdown table parsing utilities.

Extracted from sync_data.py so both sync and synthesis scripts can reuse
the same table-parsing logic.
"""

from __future__ import annotations

from pathlib import Path


def is_real_row(row: dict) -> bool:
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


def parse_md_tables(path: Path) -> list[dict]:
    """Parse all markdown tables from a file.

    Returns a list of dicts, each with 'section' (nearest heading),
    'columns' (list of column names), and 'rows' (list of dicts).
    """
    if not path.is_file():
        return []

    lines = path.read_text().splitlines()
    return parse_md_tables_from_lines(lines)


def parse_md_tables_from_lines(lines: list[str]) -> list[dict]:
    """Parse markdown tables from a list of lines (no file I/O)."""
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

            if i + 1 < len(lines) and "---" in lines[i + 1]:
                i += 2
            else:
                i += 1
                continue

            rows: list[dict] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].split("|")[1:-1]]
                if len(cells) >= len(cols):
                    row = {cols[j]: cells[j] for j in range(len(cols))}
                    if is_real_row(row):
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
