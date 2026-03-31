"""INVENTORY.md table parsing, row update/insert, and canonical counts."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from . import config

# Columns in the Repository Catalog table (order matters).
COLUMNS = ["Repo", "Surface", "Purpose", "Owner", "Tech", "Prod Status", "Audit Status", "Notes"]


def _parse_table(lines: list[str]) -> tuple[int, int, list[dict[str, str]]]:
    """Find the Repository Catalog table and parse it.

    Returns (header_line_idx, end_line_idx, rows_as_dicts).
    """
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| Repo") and "Surface" in line:
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Could not find Repository Catalog table in INVENTORY.md")

    # Skip the separator line (|---|---|...)
    data_start = header_idx + 2
    rows: list[dict[str, str]] = []
    end_idx = data_start

    for i in range(data_start, len(lines)):
        line = lines[i].strip()
        if not line.startswith("|"):
            end_idx = i
            break
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= len(COLUMNS):
            row = {COLUMNS[j]: cells[j] for j in range(len(COLUMNS))}
            rows.append(row)
        end_idx = i + 1

    return header_idx, end_idx, rows


def _row_to_line(row: dict[str, str]) -> str:
    cells = [row.get(col, "—") for col in COLUMNS]
    return "| " + " | ".join(cells) + " |"


def _rebuild_table(rows: list[dict[str, str]]) -> list[str]:
    header = "| " + " | ".join(COLUMNS) + " |"
    separator = "|" + "|".join(["---"] * len(COLUMNS)) + "|"
    lines = [header, separator]
    for row in rows:
        lines.append(_row_to_line(row))
    return lines


def _clean_value(val: str) -> str:
    """Strip italic markers and whitespace from a value."""
    return val.strip().strip("_").strip()


def _update_counts(content: str, rows: list[dict[str, str]]) -> str:
    """Update the Canonical Counts table at the top of the file."""
    total = len(rows)
    audited = sum(1 for r in rows if _clean_value(r.get("Audit Status", "")) == "complete")
    coverage = f"{audited / total * 100:.0f}%" if total > 0 else "—"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    content = re.sub(
        r"\| Total repos \| .* \|",
        f"| Total repos | {total} |",
        content,
    )
    content = re.sub(
        r"\| Audited \| .* \|",
        f"| Audited | {audited} |",
        content,
    )
    content = re.sub(
        r"\| Coverage \| .* \|",
        f"| Coverage | {coverage} |",
        content,
    )
    content = re.sub(
        r"\| Last updated \| .* \|",
        f"| Last updated | {now} |",
        content,
    )
    return content


def update_inventory(
    repo_name: str,
    purpose: str = "",
    tech: str = "",
    prod_status: str = "",
    audit_status: str = "complete",
    surface: str = "",
    owner: str = "",
) -> None:
    """Update or insert a repo row in INVENTORY.md and refresh counts."""
    path = config.INVENTORY_PATH
    content = path.read_text()
    lines = content.splitlines()

    header_idx, end_idx, rows = _parse_table(lines)

    # Find existing row by repo name (case-insensitive, strip italic markers)
    found_idx = None
    for i, row in enumerate(rows):
        if _clean_value(row["Repo"]).lower() == repo_name.lower():
            found_idx = i
            break

    if found_idx is not None:
        row = rows[found_idx]
        if tech:
            row["Tech"] = tech
        if prod_status:
            row["Prod Status"] = prod_status
        if purpose:
            row["Purpose"] = purpose
        if surface:
            row["Surface"] = surface
        if owner:
            row["Owner"] = owner
        row["Audit Status"] = audit_status
    else:
        rows.append({
            "Repo": repo_name,
            "Surface": surface or "—",
            "Purpose": purpose or "—",
            "Owner": owner or "unknown",
            "Tech": tech or "unknown",
            "Prod Status": prod_status or "unknown",
            "Audit Status": audit_status,
            "Notes": "—",
        })

    # Rebuild the table section
    new_table_lines = _rebuild_table(rows)
    new_lines = lines[:header_idx] + new_table_lines + lines[end_idx:]
    new_content = "\n".join(new_lines)

    # Update counts
    new_content = _update_counts(new_content, rows)

    # Remove example notice if real data is present
    real_rows = [r for r in rows if not r["Repo"].startswith("_")]
    if real_rows:
        new_content = new_content.replace(
            "> Replace the italic example rows above with real repos as you begin inventorying.\n",
            "",
        )

    path.write_text(new_content + "\n")


def flag_removed_repos(active_repo_names: set[str]) -> list[str]:
    """Mark repos in INVENTORY.md that are no longer in the org.

    Returns list of repos that were flagged.
    """
    path = config.INVENTORY_PATH
    content = path.read_text()
    lines = content.splitlines()
    header_idx, end_idx, rows = _parse_table(lines)

    flagged: list[str] = []
    for row in rows:
        name = _clean_value(row["Repo"])
        if name and name.lower() not in {n.lower() for n in active_repo_names}:
            if "no longer in org" not in row.get("Notes", ""):
                existing_notes = row.get("Notes", "").strip()
                if existing_notes and existing_notes != "—":
                    row["Notes"] = f"{existing_notes}; no longer in org"
                else:
                    row["Notes"] = "no longer in org"
                flagged.append(name)

    if flagged:
        new_table_lines = _rebuild_table(rows)
        new_lines = lines[:header_idx] + new_table_lines + lines[end_idx:]
        path.write_text("\n".join(new_lines) + "\n")

    return flagged


def parse_audit_report(audit_path: Path) -> dict[str, str]:
    """Extract key fields from an audit report's Identity and Tech Stack tables."""
    content = audit_path.read_text()
    fields: dict[str, str] = {}

    for line in content.splitlines():
        if "|" not in line or line.strip().startswith("|---"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) == 2:
            key, val = cells[0].strip(), cells[1].strip()
            key_lower = key.lower()
            if key_lower == "purpose":
                fields["purpose"] = val
            elif key_lower == "language(s)":
                fields["tech"] = val
            elif key_lower == "prod status":
                fields["prod_status"] = val
            elif key_lower == "owner(s)":
                fields["owner"] = val

    return fields
