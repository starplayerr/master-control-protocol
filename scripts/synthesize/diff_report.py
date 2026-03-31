#!/usr/bin/env python3
"""Diff report generator.

After synthesis runs, generates a human-readable diff showing what changed
across all maps/data/ JSON files. Suitable for PR descriptions, Slack
messages, or commit logs.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import click
import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config


# ── Snapshot and comparison ──────────────────────────────────────────────────

DATA_FILES = {
    "contradictions": {
        "path": "contradictions-and-ambiguities.json",
        "key": "items",
        "id_field": "id",
        "label": "Contradictions",
        "prose": "contradictions-and-ambiguities.md",
    },
    "stale-assumptions": {
        "path": "stale-assumptions.json",
        "key": "items",
        "id_field": "id",
        "label": "Stale Assumptions",
        "prose": "stale-assumptions.md",
    },
    "simplifications": {
        "path": "candidate-simplifications.json",
        "key": "candidates",
        "id_field": "id",
        "label": "Simplification Candidates",
        "prose": "candidate-simplifications.md",
    },
    "dependencies": {
        "path": "dependency-matrix.json",
        "key": "edges",
        "id_field": None,
        "label": "Dependency Edges",
        "prose": "dependency-matrix.md",
    },
}


def _load_data(filename: str) -> list[dict]:
    path = config.MAPS_DATA_DIR / filename
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text())
        key = next(
            (v["key"] for v in DATA_FILES.values() if v["path"] == filename), "items"
        )
        return data.get(key, [])
    except (json.JSONDecodeError, OSError):
        return []


def _item_key(item: dict, id_field: str | None) -> str:
    """Generate a stable key for comparison."""
    if id_field and id_field in item:
        return item[id_field]
    # For edges, use from+to+type
    return f"{item.get('from', '')}:{item.get('to', '')}:{item.get('type', '')}"


def take_snapshot() -> dict[str, list[dict]]:
    """Capture current state of all data files."""
    snapshot = {}
    for name, info in DATA_FILES.items():
        snapshot[name] = _load_data(info["path"])
    return snapshot


def compute_diff(before: dict[str, list[dict]], after: dict[str, list[dict]]) -> dict:
    """Compare before/after snapshots and produce a structured diff."""
    result = {}

    for name, info in DATA_FILES.items():
        old_items = before.get(name, [])
        new_items = after.get(name, [])
        id_field = info["id_field"]

        old_keys = {_item_key(i, id_field) for i in old_items}
        new_keys = {_item_key(i, id_field) for i in new_items}

        added_keys = new_keys - old_keys
        removed_keys = old_keys - new_keys

        added = [i for i in new_items if _item_key(i, id_field) in added_keys]
        removed = [i for i in old_items if _item_key(i, id_field) in removed_keys]

        result[name] = {
            "label": info["label"],
            "before_count": len(old_items),
            "after_count": len(new_items),
            "added": added,
            "removed": removed,
        }

    return result


# ── Formatting ───────────────────────────────────────────────────────────────


def _item_summary(item: dict) -> str:
    """One-line summary of an item for display."""
    item_id = item.get("id", "")
    summary = item.get("summary", item.get("title", item.get("assumption", "")))
    if item_id:
        return f"{item_id}: {summary}"
    # Edge
    return f"{item.get('from', '?')} -> {item.get('to', '?')} ({item.get('type', '?')})"


def format_text(diff: dict) -> str:
    """Human-readable diff report."""
    lines = [
        f"=== Synthesis Report ({date.today().isoformat()}) ===",
        "",
    ]

    any_changes = False

    for name, info in diff.items():
        added = info["added"]
        removed = info["removed"]

        if added:
            any_changes = True
            lines.append(f"New {info['label'].lower()}: {len(added)}")
            for item in added:
                lines.append(f"  {_item_summary(item)}")
            lines.append("")

        if removed:
            any_changes = True
            lines.append(f"Resolved {info['label'].lower()}: {len(removed)}")
            for item in removed:
                lines.append(f"  {_item_summary(item)}")
            lines.append("")

    if not any_changes:
        lines.append("No changes detected.")
        lines.append("")

    # Maps updated
    updated_maps = []
    for name, info in DATA_FILES.items():
        prose_path = config.MAPS_DIR / info["prose"]
        if prose_path.is_file():
            try:
                post = frontmatter.load(str(prose_path))
                freshness = post.metadata.get("freshness", "unknown")
                updated_maps.append(f"  {info['prose']} (freshness: {freshness})")
            except Exception:
                updated_maps.append(f"  {info['prose']} (freshness: unknown)")

    if updated_maps:
        lines.append(f"Maps updated: {len(updated_maps)}")
        lines.extend(updated_maps)

    return "\n".join(lines)


def format_json(diff: dict) -> str:
    """JSON-formatted diff report."""
    output = {
        "date": date.today().isoformat(),
        "changes": {},
    }

    for name, info in diff.items():
        output["changes"][name] = {
            "label": info["label"],
            "before_count": info["before_count"],
            "after_count": info["after_count"],
            "added_count": len(info["added"]),
            "removed_count": len(info["removed"]),
            "added": info["added"],
            "removed": info["removed"],
        }

    return json.dumps(output, indent=2)


# ── Main ─────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
@click.option(
    "--before",
    "before_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to a saved before-snapshot JSON (from --save-snapshot)",
)
@click.option(
    "--save-snapshot",
    "snapshot_path",
    type=click.Path(),
    default=None,
    help="Save current state as a snapshot for later comparison",
)
def main(as_json: bool, before_path: str | None, snapshot_path: str | None) -> None:
    """Generate a diff report of synthesis changes."""
    current = take_snapshot()

    if snapshot_path:
        Path(snapshot_path).write_text(json.dumps(current, indent=2) + "\n")
        print(f"Snapshot saved to {snapshot_path}")
        return

    if before_path:
        before = json.loads(Path(before_path).read_text())
    else:
        before = {name: [] for name in DATA_FILES}

    diff = compute_diff(before, current)

    if as_json:
        print(format_json(diff))
    else:
        print(format_text(diff))


if __name__ == "__main__":
    main()
