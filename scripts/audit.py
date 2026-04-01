#!/usr/bin/env python3
"""Audit runner: clone a repo, gather context, call LLM, produce structured report."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import config
from lib.cache import check_staleness, prompt_hash, record_audit
from lib.context import cleanup_clone, gather_context, get_head_sha, shallow_clone
from lib.inventory import parse_audit_report, update_inventory
from lib.llm import LLMClient
from lib.prompts import select_prompt
from feedback.capture import run_capture


def _build_frontmatter(repo_name: str, timestamp: str) -> str:
    date_str = timestamp[:10]
    return (
        f"---\n"
        f'title: "Audit: {repo_name}"\n'
        f"role: audit\n"
        f"last_updated: {date_str}\n"
        f"depends_on: []\n"
        f"freshness: current\n"
        f"scope: per-repo\n"
        f"---\n\n"
    )


def _build_metadata_comment(
    timestamp: str,
    commit_sha: str,
    prompt_name: str,
    p_hash: str,
    model: str,
    context_files: int,
    context_chars: int,
) -> str:
    return (
        f"<!-- audit-meta\n"
        f"timestamp: {timestamp}\n"
        f"commit_sha: {commit_sha}\n"
        f"prompt: {prompt_name}\n"
        f"prompt_hash: {p_hash}\n"
        f"model: {model}\n"
        f"context_files: {context_files}\n"
        f"context_chars: {context_chars}\n"
        f"-->\n\n"
    )


def run_audit(
    repo_url: str,
    branch: str | None = None,
    prompt_override: str | None = None,
    provider: str = config.DEFAULT_PROVIDER,
    model: str | None = None,
    context_budget: int = config.DEFAULT_CONTEXT_BUDGET,
    force: bool = False,
    interactive_capture: bool = False,
) -> Path | None:
    """Run a full audit on a single repo. Returns the path to the audit file, or None if skipped."""
    # Derive repo name from URL
    repo_name = repo_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    click.echo(f"Auditing {repo_name}...")
    clone_path = None

    try:
        # Clone
        click.echo(f"  Cloning {repo_url}...")
        clone_path = shallow_clone(repo_url, branch)
        head_sha = get_head_sha(clone_path)

        # Select prompt
        prompt_name, prompt_content = select_prompt(clone_path, prompt_override)
        p_hash = prompt_hash(prompt_content)
        click.echo(f"  Prompt: {prompt_name} (hash: {p_hash})")

        # Check cache
        if not force:
            staleness = check_staleness(repo_name, head_sha, p_hash)
            if staleness == "current":
                click.echo(f"  Skipped: already current (SHA {head_sha[:8]}, prompt {p_hash})")
                return None
            click.echo(f"  Status: {staleness}")

        # Gather context
        click.echo("  Gathering context...")
        ctx = gather_context(clone_path, budget=context_budget)
        click.echo(f"  Included {len(ctx.included)} files ({ctx.total_chars:,} chars)")
        if ctx.excluded:
            click.echo(f"  Excluded {len(ctx.excluded)} files (budget/skip)")

        # Call LLM
        resolved_model = model or config.DEFAULT_MODEL.get(provider, "")
        click.echo(f"  Calling {provider} ({resolved_model})...")
        client = LLMClient(provider=provider, model=model)
        report = client.generate(
            system_prompt=prompt_content,
            user_content=ctx.to_prompt_string(),
        )

        # Build output
        timestamp = datetime.now(timezone.utc).isoformat()
        front = _build_frontmatter(repo_name, timestamp)
        metadata = _build_metadata_comment(
            timestamp=timestamp,
            commit_sha=head_sha,
            prompt_name=prompt_name,
            p_hash=p_hash,
            model=resolved_model,
            context_files=len(ctx.included),
            context_chars=ctx.total_chars,
        )

        output_path = config.AUDITS_DIR / f"{repo_name}.md"
        config.AUDITS_DIR.mkdir(parents=True, exist_ok=True)
        output_path.write_text(front + metadata + report)
        click.echo(f"  Saved: {output_path}")

        # Update cache
        record_audit(
            repo_name=repo_name,
            commit_sha=head_sha,
            prompt_name=prompt_name,
            prompt_hash_val=p_hash,
            model=resolved_model,
        )

        # Update inventory
        audit_fields = parse_audit_report(output_path)
        update_inventory(
            repo_name=repo_name,
            purpose=audit_fields.get("purpose", ""),
            tech=audit_fields.get("tech", ""),
            prod_status=audit_fields.get("prod_status", ""),
            owner=audit_fields.get("owner", ""),
            audit_status="complete",
        )
        click.echo(f"  Updated INVENTORY.md")

        # Post-audit knowledge capture
        try:
            capture_result = run_capture(output_path, interactive=interactive_capture)
            n_findings = len(capture_result.get("captures", []))
            if n_findings:
                click.echo(f"  Feedback captured: {n_findings} automated findings")
        except Exception as e:
            click.echo(f"  Warning: feedback capture failed: {e}", err=True)

        return output_path

    finally:
        if clone_path:
            cleanup_clone(clone_path)


@click.command()
@click.option("--repo", required=True, help="Repository URL to audit")
@click.option("--branch", default=None, help="Branch to audit (default: repo default branch)")
@click.option("--prompt", "prompt_override", default=None, help="Prompt name override (e.g., infrastructure, service)")
@click.option("--provider", default=config.DEFAULT_PROVIDER, type=click.Choice(["anthropic", "openai"]))
@click.option("--model", default=None, help="Specific model name")
@click.option("--context-budget", default=config.DEFAULT_CONTEXT_BUDGET, type=int, help="Max context chars")
@click.option("--force", is_flag=True, help="Re-audit even if current")
@click.option("--interactive-capture", is_flag=True, help="Prompt for manual feedback after audit")
def main(repo: str, branch: str | None, prompt_override: str | None, provider: str, model: str | None, context_budget: int, force: bool, interactive_capture: bool):
    """Run a structured audit on a single repository."""
    result = run_audit(
        repo_url=repo,
        branch=branch,
        prompt_override=prompt_override,
        provider=provider,
        model=model,
        context_budget=context_budget,
        force=force,
        interactive_capture=interactive_capture,
    )
    if result:
        click.echo(f"\nAudit complete: {result}")
    else:
        click.echo("\nAudit skipped (already current). Use --force to re-audit.")


if __name__ == "__main__":
    main()
