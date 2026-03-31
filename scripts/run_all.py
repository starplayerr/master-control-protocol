#!/usr/bin/env python3
"""Orchestrator: discover -> filter -> check cache -> audit (parallel) -> update inventory."""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import config
from lib.cache import check_staleness, prompt_hash
from lib.context import get_head_sha, shallow_clone, cleanup_clone
from lib.inventory import flag_removed_repos
from lib.prompts import select_prompt


def _load_discovered() -> list[dict]:
    """Load the most recent discovered.json."""
    if not config.DISCOVERED_PATH.is_file():
        return []
    data = json.loads(config.DISCOVERED_PATH.read_text())
    return data.get("repos", [])


def _quick_staleness_check(repo: dict) -> str:
    """Check staleness using discovered.json SHA (no clone needed)."""
    # We need the prompt hash too — use default prompt as a rough check.
    # Full check happens during audit when the actual prompt is selected.
    try:
        default_prompt = (config.PROMPTS_DIR / "default.md").read_text()
        p_hash = prompt_hash(default_prompt)
    except FileNotFoundError:
        return "never-audited"

    sha = repo.get("last_commit_sha", "")
    if not sha:
        return "never-audited"

    return check_staleness(repo["name"], sha, p_hash)


async def _audit_one(
    repo: dict,
    provider: str,
    model: str | None,
    force: bool,
    semaphore: asyncio.Semaphore,
) -> tuple[str, str]:
    """Audit a single repo. Returns (repo_name, status)."""
    from audit import run_audit

    async with semaphore:
        repo_name = repo["name"]
        try:
            result = await asyncio.to_thread(
                run_audit,
                repo_url=repo["url"],
                branch=repo.get("default_branch"),
                provider=provider,
                model=model,
                force=force,
            )
            if result is None:
                return repo_name, "skipped"
            return repo_name, "audited"
        except Exception as e:
            click.echo(f"  ERROR [{repo_name}]: {e}", err=True)
            return repo_name, "failed"


async def _run_pipeline(
    org: str | None,
    repos_list: str | None,
    concurrency: int,
    provider: str,
    model: str | None,
    force: bool,
    dry_run: bool,
) -> None:
    start_time = time.time()

    # Step 1: Discover or load explicit repo list
    if org:
        from discover import _enumerate_repos
        click.echo(f"Discovering repos in {org}...")
        token = config.GITHUB_TOKEN
        if not token:
            click.echo("Error: GITHUB_TOKEN required.", err=True)
            raise SystemExit(1)
        repos = _enumerate_repos(org, token, skip_archived=True, skip_forks=True, min_size=0)
        # Save discovered.json
        output = {
            "org": org,
            "discovered_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "repos": repos,
        }
        config.DISCOVERED_PATH.write_text(json.dumps(output, indent=2) + "\n")
        click.echo(f"Discovered {len(repos)} repos")
    elif repos_list:
        repos = [{"name": r.split("/")[-1], "url": r, "default_branch": None} for r in repos_list.split(",")]
        click.echo(f"Using {len(repos)} explicit repos")
    else:
        repos = _load_discovered()
        if not repos:
            click.echo("Error: No repos. Run with --org or --repos, or run discover.py first.", err=True)
            raise SystemExit(1)
        click.echo(f"Loaded {len(repos)} repos from discovered.json")

    # Step 2: Check cache / classify
    to_audit: list[dict] = []
    skipped = 0
    for repo in repos:
        if force:
            to_audit.append(repo)
            continue
        status = _quick_staleness_check(repo)
        if status == "current":
            skipped += 1
        else:
            to_audit.append(repo)

    click.echo(f"\nTo audit: {len(to_audit)}, Already current: {skipped}")

    if dry_run:
        click.echo("\n[DRY RUN] Would audit:")
        for r in to_audit:
            click.echo(f"  {r['name']}")
        return

    if not to_audit:
        click.echo("Nothing to audit.")
        return

    # Step 3: Audit in parallel
    click.echo(f"\nAuditing with concurrency={concurrency}...\n")
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        _audit_one(repo, provider, model, force, semaphore)
        for repo in to_audit
    ]
    results = await asyncio.gather(*tasks)

    # Step 4: Flag removed repos
    if org:
        active_names = {r["name"] for r in repos}
        flagged = flag_removed_repos(active_names)
        if flagged:
            click.echo(f"\nFlagged {len(flagged)} repos no longer in org: {', '.join(flagged)}")

    # Step 5: Summary
    audited = sum(1 for _, s in results if s == "audited")
    failed = sum(1 for _, s in results if s == "failed")
    run_skipped = sum(1 for _, s in results if s == "skipped")
    elapsed = time.time() - start_time

    click.echo(f"\n{'=' * 50}")
    click.echo(f"Discovered: {len(repos)} repos")
    click.echo(f"Audited:    {audited}")
    click.echo(f"Skipped:    {skipped + run_skipped} (current)")
    click.echo(f"Failed:     {failed}")
    click.echo(f"Duration:   {elapsed:.0f}s")
    click.echo(f"{'=' * 50}")


@click.command()
@click.option("--org", default=None, help="GitHub org name to discover and audit")
@click.option("--repos", "repos_list", default=None, help="Comma-separated repo URLs (alternative to --org)")
@click.option("--concurrency", default=config.DEFAULT_CONCURRENCY, type=int, help="Parallel audit workers")
@click.option("--provider", default=config.DEFAULT_PROVIDER, type=click.Choice(["anthropic", "openai"]))
@click.option("--model", default=None, help="Specific model name")
@click.option("--force", is_flag=True, help="Re-audit everything regardless of cache")
@click.option("--dry-run", is_flag=True, help="Discover and check cache without auditing")
def main(org, repos_list, concurrency, provider, model, force, dry_run):
    """Run the full MCP audit pipeline: discover -> audit -> update inventory."""
    if not org and not repos_list:
        # Try loading existing discovered.json
        if not config.DISCOVERED_PATH.is_file():
            click.echo("Error: Provide --org or --repos, or run discover.py first.", err=True)
            raise SystemExit(1)

    asyncio.run(_run_pipeline(org, repos_list, concurrency, provider, model, force, dry_run))


if __name__ == "__main__":
    main()
