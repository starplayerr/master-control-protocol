#!/usr/bin/env python3
"""Post-audit knowledge capture.

After each audit, extracts reusable learnings:
- New patterns discovered
- Prompt gaps (things the prompt should have asked about)
- Corrections (audit said X, reality is Y)
- Cross-repo insights
- Unknown resolutions (previously unknown fields now known)

Supports interactive mode (prompts the user) and automated mode
(compares audit output against existing maps for contradictions).

Storage: feedback/capture-log.jsonl (append-only)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from synthesize.extract import AuditFacts, load_all_audits, extract_facts

CAPTURE_TYPES = ["pattern", "prompt-gap", "correction", "cross-repo-insight", "unknown-resolution"]


# ── Storage ──────────────────────────────────────────────────────────────────


def _append_capture(entry: dict) -> None:
    """Append a single capture entry to the JSONL log."""
    config.FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.CAPTURE_LOG_PATH, "a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def load_capture_log() -> list[dict]:
    """Load all entries from the capture log."""
    if not config.CAPTURE_LOG_PATH.is_file():
        return []
    entries = []
    for line in config.CAPTURE_LOG_PATH.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


# ── Automated capture ────────────────────────────────────────────────────────


def _check_unknown_fields(facts: AuditFacts) -> list[dict]:
    """Find fields that are still 'unknown' — potential prompt gaps."""
    gaps = []
    unknown_markers = {"unknown", "n/a", "—", "", "?"}

    field_checks = [
        ("identity.owners", facts.identity.owners),
        ("identity.prod_status", facts.identity.prod_status),
        ("identity.purpose", facts.identity.purpose),
        ("tech_stack.languages", facts.tech_stack.languages),
        ("tech_stack.frameworks", facts.tech_stack.frameworks),
        ("tech_stack.build_tools", facts.tech_stack.build_tools),
        ("deployment.ci", facts.deployment.ci),
        ("deployment.cd", facts.deployment.cd),
        ("deployment.targets", facts.deployment.targets),
        ("package.version", facts.package.version),
        ("package.registry", facts.package.registry),
    ]

    for field_path, value in field_checks:
        if value.strip().lower() in unknown_markers:
            gaps.append({
                "type": "prompt-gap",
                "detail": f"Field '{field_path}' is '{value}' — prompt may not have extracted this",
                "field": field_path,
                "suggested_prompt_change": f"Ensure the prompt specifically asks about {field_path.split('.')[-1]}",
            })

    return gaps


def _check_map_contradictions(
    facts: AuditFacts,
    existing_facts: dict[str, AuditFacts],
) -> list[dict]:
    """Compare this audit against existing audits for cross-repo contradictions."""
    captures = []
    repo_name = facts.identity.repo_name

    for dep in facts.outbound_deps:
        dep_name = dep.get("dependency", "").split("==")[0].split(">=")[0].strip()
        for other_name, other_facts in existing_facts.items():
            if other_name == repo_name:
                continue
            if dep_name.lower() == other_name.lower():
                if facts.package.version and other_facts.package.version:
                    if facts.package.version != other_facts.package.version:
                        captures.append({
                            "type": "cross-repo-insight",
                            "detail": (
                                f"{repo_name} depends on {dep_name} "
                                f"but version mismatch: "
                                f"{dep.get('dependency', '')} vs "
                                f"{other_facts.package.version}"
                            ),
                            "affects": f"audits/{other_name}.md",
                        })

    for gap in facts.known_gaps:
        for other_name in existing_facts:
            if other_name == repo_name:
                continue
            if other_name.lower() in gap.lower():
                captures.append({
                    "type": "cross-repo-insight",
                    "detail": f"{repo_name} audit mentions {other_name} in known gaps: {gap}",
                    "affects": f"audits/{other_name}.md",
                })

    return captures


def _check_unknown_resolutions(
    facts: AuditFacts,
    capture_log: list[dict],
) -> list[dict]:
    """Check if any previously-unknown fields are now resolved."""
    resolutions = []
    repo_name = facts.identity.repo_name

    prev_unknowns = [
        e for e in capture_log
        if e.get("audit", "").endswith(f"{repo_name}.md")
        and any(c.get("type") == "prompt-gap" and "unknown" in c.get("detail", "").lower()
                for c in e.get("captures", []))
    ]

    if not prev_unknowns:
        return resolutions

    unknown_markers = {"unknown", "n/a", "—", "", "?"}
    field_values = {
        "identity.owners": facts.identity.owners,
        "identity.prod_status": facts.identity.prod_status,
        "identity.purpose": facts.identity.purpose,
        "tech_stack.languages": facts.tech_stack.languages,
        "deployment.ci": facts.deployment.ci,
        "deployment.cd": facts.deployment.cd,
        "package.version": facts.package.version,
    }

    for entry in prev_unknowns:
        for cap in entry.get("captures", []):
            field = cap.get("field", "")
            if field in field_values and field_values[field].strip().lower() not in unknown_markers:
                resolutions.append({
                    "type": "unknown-resolution",
                    "detail": f"Field '{field}' was unknown, now resolved to '{field_values[field]}'",
                    "field": field,
                    "resolved_value": field_values[field],
                })

    return resolutions


def automated_capture(audit_path: Path) -> dict:
    """Run automated capture after an audit. Returns the capture entry."""
    facts = extract_facts(audit_path)
    repo_name = facts.identity.repo_name or audit_path.stem
    existing = load_all_audits(use_cache=True)
    capture_log = load_capture_log()

    captures: list[dict] = []
    captures.extend(_check_unknown_fields(facts))
    captures.extend(_check_map_contradictions(facts, existing))
    captures.extend(_check_unknown_resolutions(facts, capture_log))

    entry = {
        "audit": str(audit_path.relative_to(config.MCP_ROOT)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "automated",
        "captures": captures,
    }

    if captures:
        _append_capture(entry)

    return entry


# ── Interactive capture ──────────────────────────────────────────────────────


def interactive_capture(audit_path: Path) -> dict:
    """Prompt the user for post-audit feedback. Returns the capture entry."""
    repo_name = audit_path.stem
    click.echo(f"\n{'=' * 60}")
    click.echo(f"POST-AUDIT FEEDBACK: {repo_name}")
    click.echo(f"{'=' * 60}")

    captures: list[dict] = []

    # Q1: Missed patterns
    click.echo("\n1. Did the audit miss anything important about this repo?")
    click.echo("   (e.g., unusual deployment patterns, hidden dependencies)")
    response = click.prompt("   Your answer (or 'skip')", default="skip")
    if response.lower() != "skip":
        captures.append({
            "type": "prompt-gap",
            "detail": response,
            "suggested_prompt_change": f"Add detection for: {response}",
        })

    # Q2: Incorrect findings
    click.echo("\n2. Were any findings incorrect?")
    click.echo("   (e.g., wrong deployment target, incorrect tech stack)")
    response = click.prompt("   Your answer (or 'skip')", default="skip")
    if response.lower() != "skip":
        field = click.prompt("   Which field was wrong?", default="unspecified")
        actual = click.prompt("   What's the correct value?", default="unspecified")
        captures.append({
            "type": "correction",
            "detail": response,
            "field": field,
            "audit_said": "see audit report",
            "actual": actual,
            "corrected_by": "human",
        })

    # Q3: Cross-repo insights
    click.echo("\n3. Did you learn something about OTHER repos from this audit?")
    click.echo("   (e.g., discovered undocumented dependency on repo X)")
    response = click.prompt("   Your answer (or 'skip')", default="skip")
    if response.lower() != "skip":
        affected = click.prompt("   Which repo(s) does this affect?", default="unknown")
        captures.append({
            "type": "cross-repo-insight",
            "detail": response,
            "affects": f"audits/{affected}.md" if affected != "unknown" else "unknown",
        })

    # Q4: New patterns
    click.echo("\n4. Any new patterns worth remembering?")
    click.echo("   (e.g., repo uses unconventional monorepo structure)")
    response = click.prompt("   Your answer (or 'skip')", default="skip")
    if response.lower() != "skip":
        captures.append({
            "type": "pattern",
            "detail": response,
        })

    entry = {
        "audit": str(audit_path.relative_to(config.MCP_ROOT)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "interactive",
        "captures": captures,
    }

    if captures:
        _append_capture(entry)
        click.echo(f"\n  Captured {len(captures)} feedback items.")
    else:
        click.echo("\n  No feedback captured.")

    return entry


# ── Combined runner ──────────────────────────────────────────────────────────


def run_capture(audit_path: Path, interactive: bool = False) -> dict:
    """Run both automated and optionally interactive capture.

    Returns a merged capture entry with all findings.
    """
    auto_entry = automated_capture(audit_path)
    all_captures = list(auto_entry.get("captures", []))

    if interactive:
        human_entry = interactive_capture(audit_path)
        all_captures.extend(human_entry.get("captures", []))

    result = {
        "audit": str(audit_path.relative_to(config.MCP_ROOT)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "interactive" if interactive else "automated",
        "captures": all_captures,
        "auto_findings": len(auto_entry.get("captures", [])),
        "human_findings": len(all_captures) - len(auto_entry.get("captures", [])),
    }

    return result


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--audit", required=True, help="Path to audit file (relative to MCP root or absolute)")
@click.option("--interactive/--no-interactive", default=False, help="Enable interactive mode")
def main(audit: str, interactive: bool) -> None:
    """Run post-audit knowledge capture."""
    audit_path = Path(audit)
    if not audit_path.is_absolute():
        audit_path = config.MCP_ROOT / audit_path
    if not audit_path.is_file():
        click.echo(f"Error: audit file not found: {audit_path}", err=True)
        raise SystemExit(1)

    result = run_capture(audit_path, interactive=interactive)
    n = len(result["captures"])
    click.echo(f"\nCapture complete: {n} items ({result['auto_findings']} auto, {result['human_findings']} human)")


if __name__ == "__main__":
    main()
