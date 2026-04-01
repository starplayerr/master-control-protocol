#!/usr/bin/env python3
"""Prompt evolution engine.

Aggregates feedback from the capture log to suggest (and optionally apply)
improvements to audit prompts.

Workflow:
1. Aggregate all prompt-gap captures for each prompt variant
2. Use LLM to cluster gaps by theme and generate proposed additions
3. Write proposals to feedback/prompt-proposals.md for human review
4. On approval (--apply), append to the prompt and bump the version hash
   so the audit cache detects the change and triggers re-audits

Storage: feedback/prompt-proposals.md
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from lib.cache import prompt_hash
from lib.llm import LLMClient
from feedback.capture import load_capture_log

CLUSTER_SYSTEM_PROMPT = """\
You are an expert at improving audit prompts for repository analysis.

Given a list of "prompt gaps" — things that audits missed — group them into
clusters by theme. For each cluster, propose a concrete addition to the
audit prompt that would catch these gaps in future audits.

Output valid JSON with this structure:
{
  "clusters": [
    {
      "theme": "short theme name",
      "gaps": ["gap detail 1", "gap detail 2"],
      "source_audits": ["audits/repo1.md", "audits/repo2.md"],
      "proposed_addition": "The exact text to add to the prompt template"
    }
  ]
}

Rules:
- Group similar gaps even if worded differently
- Each proposed_addition should be a specific, actionable instruction
- Keep additions concise (2-4 sentences max)
- Don't propose additions that duplicate existing prompt content
"""


def _collect_gaps_by_prompt(capture_log: list[dict], audit_state: dict) -> dict[str, list[dict]]:
    """Group prompt-gap captures by the prompt variant that produced them."""
    repo_to_prompt: dict[str, str] = {}
    for repo_name, state in audit_state.get("repos", {}).items():
        prompt_name = state.get("prompt_name", "default")
        repo_to_prompt[repo_name] = f"prompts/{prompt_name}.md"

    gaps_by_prompt: dict[str, list[dict]] = defaultdict(list)

    for entry in capture_log:
        audit_file = entry.get("audit", "")
        repo_name = Path(audit_file).stem
        prompt_file = repo_to_prompt.get(repo_name, "prompts/default.md")

        for cap in entry.get("captures", []):
            if cap.get("type") == "prompt-gap":
                gaps_by_prompt[prompt_file].append({
                    "detail": cap.get("detail", ""),
                    "field": cap.get("field", ""),
                    "audit": audit_file,
                    "suggested": cap.get("suggested_prompt_change", ""),
                })

    return dict(gaps_by_prompt)


def _cluster_gaps_with_llm(
    gaps: list[dict],
    prompt_file: str,
    provider: str,
    model: str | None,
) -> list[dict]:
    """Use the LLM to cluster gaps and generate proposed additions."""
    if not gaps:
        return []

    client = LLMClient(provider=provider, model=model)
    user_content = (
        f"Prompt file: {prompt_file}\n\n"
        f"Gaps found ({len(gaps)} total):\n\n"
        + "\n".join(
            f"- [{g['audit']}] {g['detail']}"
            + (f" (field: {g['field']})" if g.get("field") else "")
            + (f"\n  Suggested: {g['suggested']}" if g.get("suggested") else "")
            for g in gaps
        )
    )

    response = client.generate(CLUSTER_SYSTEM_PROMPT, user_content)

    # Parse JSON from response (handle markdown code fences)
    text = response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
        return data.get("clusters", [])
    except json.JSONDecodeError:
        return [{
            "theme": "unclustered",
            "gaps": [g["detail"] for g in gaps],
            "source_audits": list({g["audit"] for g in gaps}),
            "proposed_addition": "Review manually — LLM clustering failed",
        }]


def _cluster_gaps_locally(gaps: list[dict]) -> list[dict]:
    """Simple local clustering by field name (no LLM needed)."""
    by_field: dict[str, list[dict]] = defaultdict(list)
    no_field: list[dict] = []

    for g in gaps:
        field = g.get("field", "")
        if field:
            by_field[field].append(g)
        else:
            no_field.append(g)

    clusters = []
    for field, field_gaps in by_field.items():
        clusters.append({
            "theme": f"Missing field: {field}",
            "gaps": [g["detail"] for g in field_gaps],
            "source_audits": sorted({g["audit"] for g in field_gaps}),
            "proposed_addition": (
                f"Ensure the prompt explicitly asks about {field.split('.')[-1]} "
                f"and provides guidance on where to find it in the repo."
            ),
        })

    if no_field:
        clusters.append({
            "theme": "General prompt gaps",
            "gaps": [g["detail"] for g in no_field],
            "source_audits": sorted({g["audit"] for g in no_field}),
            "proposed_addition": "Review these gaps manually and add targeted instructions.",
        })

    return clusters


def _write_proposals(
    all_proposals: dict[str, list[dict]],
    dry_run: bool = False,
) -> str:
    """Write proposals to feedback/prompt-proposals.md. Returns the content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "---",
        'title: "Prompt Evolution Proposals"',
        "role: template",
        f"last_updated: {now}",
        "depends_on:",
        "  - feedback/capture-log.jsonl",
        "freshness: current",
        "scope: platform",
        "---",
        "",
        f"# Prompt Evolution Proposals ({now})",
        "",
        "Auto-generated from post-audit feedback. Each proposal needs human review",
        "before being applied to prompt templates.",
        "",
    ]

    proposal_id = 0
    for prompt_file, clusters in sorted(all_proposals.items()):
        lines.append(f"## {prompt_file}")
        lines.append("")

        for cluster in clusters:
            proposal_id += 1
            theme = cluster.get("theme", "Unknown")
            gap_count = len(cluster.get("gaps", []))
            sources = cluster.get("source_audits", [])
            addition = cluster.get("proposed_addition", "")

            lines.append(f"### Proposal {proposal_id}: {theme}")
            lines.append(f"**Based on:** {gap_count} prompt-gap captures across {', '.join(sources)}")
            lines.append(f"**Gap:** {'; '.join(cluster.get('gaps', [])[:3])}")
            if gap_count > 3:
                lines.append(f"  _(and {gap_count - 3} more)_")
            lines.append(f"**Suggested addition to prompt:**")
            lines.append(f"> {addition}")
            lines.append(f"**Status:** Pending review")
            lines.append("")

    content = "\n".join(lines)

    if not dry_run:
        config.FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
        config.PROMPT_PROPOSALS_PATH.write_text(content)

    return content


def apply_proposal(prompt_file: str, addition: str) -> str:
    """Apply an approved proposal to a prompt file. Returns the new prompt hash."""
    prompt_path = config.MCP_ROOT / prompt_file
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")

    content = prompt_path.read_text()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    content += f"\n\n<!-- Added {timestamp} via prompt evolution -->\n{addition}\n"

    prompt_path.write_text(content)
    new_hash = prompt_hash(content)

    return new_hash


def evolve_prompts(
    use_llm: bool = False,
    provider: str = config.DEFAULT_PROVIDER,
    model: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Run the prompt evolution engine.

    Returns summary stats.
    """
    from lib.cache import get_state
    audit_state = get_state()
    capture_log = load_capture_log()
    gaps_by_prompt = _collect_gaps_by_prompt(capture_log, audit_state)

    if not gaps_by_prompt:
        return {"total_gaps": 0, "proposals": 0, "prompts_affected": 0}

    all_proposals: dict[str, list[dict]] = {}
    total_gaps = 0

    for prompt_file, gaps in gaps_by_prompt.items():
        total_gaps += len(gaps)
        if use_llm:
            clusters = _cluster_gaps_with_llm(gaps, prompt_file, provider, model)
        else:
            clusters = _cluster_gaps_locally(gaps)
        if clusters:
            all_proposals[prompt_file] = clusters

    _write_proposals(all_proposals, dry_run=dry_run)

    total_proposals = sum(len(c) for c in all_proposals.values())
    return {
        "total_gaps": total_gaps,
        "proposals": total_proposals,
        "prompts_affected": len(all_proposals),
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


@click.command()
@click.option("--use-llm", is_flag=True, help="Use LLM for clustering (costs API credits)")
@click.option("--provider", default=config.DEFAULT_PROVIDER, type=click.Choice(["anthropic", "openai"]))
@click.option("--model", default=None, help="Specific model name")
@click.option("--dry-run", is_flag=True, help="Don't write proposals file")
@click.option("--apply", "apply_file", default=None, help="Apply a specific prompt file's proposals (e.g., prompts/default.md)")
def main(use_llm: bool, provider: str, model: str | None, dry_run: bool, apply_file: str | None) -> None:
    """Generate prompt improvement proposals from feedback data."""
    if apply_file:
        click.echo(f"Applying proposals is interactive — edit the prompt file directly")
        click.echo(f"and re-run audits. The cache will detect the prompt hash change.")
        return

    result = evolve_prompts(use_llm=use_llm, provider=provider, model=model, dry_run=dry_run)

    click.echo(f"\n{'=' * 60}")
    click.echo("PROMPT EVOLUTION")
    click.echo(f"{'=' * 60}")
    click.echo(f"  Total gaps analyzed: {result['total_gaps']}")
    click.echo(f"  Proposals generated: {result['proposals']}")
    click.echo(f"  Prompts affected:    {result['prompts_affected']}")

    if not dry_run and result["proposals"] > 0:
        click.echo(f"\n  Proposals written to: {config.PROMPT_PROPOSALS_PATH}")
        click.echo(f"  Review and apply manually, then re-run affected audits.")


if __name__ == "__main__":
    main()
