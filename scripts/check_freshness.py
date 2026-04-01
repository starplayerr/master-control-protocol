"""Staleness propagation: detect when maps are stale relative to their dependencies."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import click
import frontmatter

ROOT = Path(__file__).resolve().parents[1]
AUDIT_STATE_PATH = ROOT / "audit-state.json"


def find_md_files() -> list[Path]:
    """Find all markdown files in the repo, excluding README.md at root."""
    files: list[Path] = []
    for md in ROOT.rglob("*.md"):
        rel = md.relative_to(ROOT)
        if rel.parts[0] in (".cursor", ".venv", "node_modules"):
            continue
        if rel == Path("README.md"):
            continue
        if rel.name in ("AGENTS.md", "CLAUDE.md"):
            continue
        if "_meta" in rel.parts:
            continue
        files.append(md)
    return sorted(files)


def parse_frontmatter(path: Path) -> dict | None:
    """Parse YAML frontmatter from a markdown file. Returns metadata dict or None."""
    try:
        post = frontmatter.load(str(path))
        if post.metadata:
            return post.metadata
    except Exception:
        pass
    return None


def resolve_depends_on(depends: list[str]) -> list[Path]:
    """Expand depends_on entries (which may contain globs) into concrete paths."""
    resolved: list[Path] = []
    for dep in depends:
        if "*" in dep:
            resolved.extend(sorted(ROOT.glob(dep)))
        else:
            target = ROOT / dep
            if target.is_file():
                resolved.append(target)
    return resolved


def get_last_updated(meta: dict | None) -> date | None:
    if meta is None:
        return None
    raw = meta.get("last_updated")
    if raw is None:
        return None
    if isinstance(raw, date):
        return raw
    try:
        return date.fromisoformat(str(raw))
    except (ValueError, TypeError):
        return None


def load_audit_state() -> dict:
    if AUDIT_STATE_PATH.is_file():
        return json.loads(AUDIT_STATE_PATH.read_text())
    return {"repos": {}}


def check_freshness_all() -> list[dict]:
    """Check freshness for all markdown files. Returns list of findings."""
    files = find_md_files()
    file_meta: dict[Path, dict | None] = {}
    for f in files:
        file_meta[f] = parse_frontmatter(f)

    audit_state = load_audit_state()
    findings: list[dict] = []

    for fpath, meta in sorted(file_meta.items()):
        rel = fpath.relative_to(ROOT)
        if meta is None:
            findings.append({
                "file": str(rel),
                "declared_freshness": None,
                "computed_freshness": "unknown",
                "reason": "no frontmatter",
                "stale_deps": [],
            })
            continue

        declared = meta.get("freshness", "unknown")
        file_date = get_last_updated(meta)
        depends = meta.get("depends_on", [])
        if not isinstance(depends, list):
            depends = []

        stale_deps: list[str] = []

        if depends and file_date:
            dep_paths = resolve_depends_on(depends)
            for dep_path in dep_paths:
                dep_meta = file_meta.get(dep_path) or parse_frontmatter(dep_path)
                dep_date = get_last_updated(dep_meta)
                if dep_date and dep_date > file_date:
                    stale_deps.append(str(dep_path.relative_to(ROOT)))

            for dep_str in depends:
                if dep_str.startswith("audits/") or dep_str == "audits/*":
                    for repo_name, repo_info in audit_state.get("repos", {}).items():
                        audit_date_str = repo_info.get("last_audit_date", "")
                        try:
                            audit_date = date.fromisoformat(audit_date_str[:10])
                            if audit_date > file_date:
                                label = f"audit-state:{repo_name}"
                                if label not in stale_deps:
                                    stale_deps.append(label)
                        except (ValueError, TypeError):
                            pass

        if stale_deps:
            computed = "stale"
            reason = f"dependencies newer: {', '.join(stale_deps)}"
        elif declared == "draft":
            computed = "draft"
            reason = "self-declared draft"
        elif declared == "stale":
            computed = "stale"
            reason = "self-declared stale"
        else:
            computed = "current"
            reason = "up to date"

        findings.append({
            "file": str(rel),
            "declared_freshness": declared,
            "computed_freshness": computed,
            "reason": reason,
            "stale_deps": stale_deps,
        })

    return findings


def fix_frontmatter(findings: list[dict]) -> int:
    """Update freshness fields in-place for files where computed != declared."""
    fixed = 0
    for f in findings:
        if f["declared_freshness"] is None:
            continue
        if f["computed_freshness"] == "unknown":
            continue
        if f["declared_freshness"] == f["computed_freshness"]:
            continue

        path = ROOT / f["file"]
        post = frontmatter.load(str(path))
        post.metadata["freshness"] = f["computed_freshness"]
        path.write_text(frontmatter.dumps(post) + "\n")
        fixed += 1
    return fixed


def print_report(findings: list[dict]) -> None:
    current = [f for f in findings if f["computed_freshness"] == "current"]
    stale = [f for f in findings if f["computed_freshness"] == "stale"]
    draft = [f for f in findings if f["computed_freshness"] == "draft"]
    unknown = [f for f in findings if f["computed_freshness"] == "unknown"]

    print("=" * 60)
    print("MCP FRESHNESS REPORT")
    print("=" * 60)
    print()

    if stale:
        print(f"STALE ({len(stale)}):")
        for f in stale:
            print(f"  ! {f['file']}")
            print(f"    {f['reason']}")
        print()

    if draft:
        print(f"DRAFT ({len(draft)}):")
        for f in draft:
            print(f"  ~ {f['file']}")
        print()

    if current:
        print(f"CURRENT ({len(current)}):")
        for f in current:
            print(f"  . {f['file']}")
        print()

    if unknown:
        print(f"UNKNOWN ({len(unknown)}):")
        for f in unknown:
            print(f"  ? {f['file']} — {f['reason']}")
        print()

    print("-" * 60)
    total = len(findings)
    print(f"Total: {total} files | "
          f"{len(current)} current | "
          f"{len(stale)} stale | "
          f"{len(draft)} draft | "
          f"{len(unknown)} unknown")


@click.command()
@click.option("--fix", is_flag=True, help="Update frontmatter freshness fields in-place.")
def main(fix: bool) -> None:
    """Check freshness of all MCP markdown files and detect staleness cascades."""
    findings = check_freshness_all()
    print_report(findings)

    stale_count = sum(1 for f in findings if f["computed_freshness"] == "stale")

    if fix and stale_count:
        print()
        fixed = fix_frontmatter(findings)
        print(f"Updated freshness in {fixed} file(s).")
    elif stale_count and not fix:
        print()
        print("Run with --fix to update frontmatter automatically.")

    sys.exit(1 if stale_count else 0)


if __name__ == "__main__":
    main()
