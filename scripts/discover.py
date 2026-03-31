#!/usr/bin/env python3
"""Repo discovery: enumerate GitHub org repos and output discovered.json."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import click
from github import Github, GithubException

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from lib import config


def _enumerate_repos(
    org: str,
    token: str,
    skip_archived: bool,
    skip_forks: bool,
    min_size: int,
) -> list[dict]:
    """Fetch all repos from a GitHub org, applying filters."""
    gh = Github(token, per_page=100)
    try:
        organization = gh.get_organization(org)
    except GithubException:
        # Might be a user account, not an org
        organization = gh.get_user(org)

    repos = []
    for repo in organization.get_repos(type="all"):
        if skip_archived and repo.archived:
            continue
        if skip_forks and repo.fork:
            continue
        if repo.size and repo.size < min_size:
            continue

        # Get last commit info from default branch
        last_sha = ""
        last_date = ""
        try:
            branch = repo.get_branch(repo.default_branch)
            last_sha = branch.commit.sha
            if branch.commit.commit.committer and branch.commit.commit.committer.date:
                last_date = branch.commit.commit.committer.date.isoformat()
        except GithubException:
            pass

        # Language breakdown (percentages)
        try:
            languages = repo.get_languages()
            byte_counts = {k: v for k, v in languages.items() if isinstance(v, (int, float))}
            total_bytes = sum(byte_counts.values()) or 1
            lang_pct = {lang: round(b / total_bytes * 100) for lang, b in byte_counts.items()}
        except (GithubException, TypeError):
            lang_pct = {}

        repos.append({
            "name": repo.name,
            "url": repo.html_url,
            "default_branch": repo.default_branch,
            "last_commit_sha": last_sha,
            "last_commit_date": last_date,
            "languages": lang_pct,
            "topics": repo.get_topics(),
            "archived": repo.archived,
            "fork": repo.fork,
            "size_kb": repo.size,
        })

    return repos


def _diff_against_inventory(repos: list[dict]) -> dict:
    """Compare discovered repos against INVENTORY.md."""
    discovered_names = {r["name"].lower() for r in repos}

    inventory_names: set[str] = set()
    if config.INVENTORY_PATH.is_file():
        for line in config.INVENTORY_PATH.read_text().splitlines():
            if line.strip().startswith("|") and not line.strip().startswith("| Repo") and "---" not in line:
                cells = [c.strip().strip("_") for c in line.split("|")[1:-1]]
                if cells and cells[0]:
                    inventory_names.add(cells[0].lower())

    new_repos = [r for r in repos if r["name"].lower() not in inventory_names]
    removed = [n for n in inventory_names if n not in discovered_names and n != ""]

    return {"new": [r["name"] for r in new_repos], "removed": list(removed)}


@click.command()
@click.option("--org", required=True, help="GitHub org (or user) name")
@click.option("--token", default=None, help="GitHub token (falls back to GITHUB_TOKEN env var)")
@click.option("--skip-archived/--include-archived", default=True, help="Skip archived repos")
@click.option("--skip-forks/--include-forks", default=True, help="Skip forked repos")
@click.option("--min-size", default=0, type=int, help="Minimum repo size in KB")
@click.option("--diff", "show_diff", is_flag=True, help="Show diff against INVENTORY.md")
def main(org: str, token: str | None, skip_archived: bool, skip_forks: bool, min_size: int, show_diff: bool):
    """Discover repos in a GitHub org and output discovered.json."""
    token = token or config.GITHUB_TOKEN
    if not token:
        click.echo("Error: GitHub token required. Set GITHUB_TOKEN or use --token.", err=True)
        raise SystemExit(1)

    click.echo(f"Discovering repos in {org}...")
    repos = _enumerate_repos(org, token, skip_archived, skip_forks, min_size)
    click.echo(f"Found {len(repos)} repos")

    output = {
        "org": org,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "repos": repos,
    }
    config.DISCOVERED_PATH.write_text(json.dumps(output, indent=2) + "\n")
    click.echo(f"Wrote {config.DISCOVERED_PATH}")

    if show_diff:
        diff = _diff_against_inventory(repos)
        if diff["new"]:
            click.echo(f"\nNew repos ({len(diff['new'])}):")
            for name in sorted(diff["new"]):
                click.echo(f"  + {name}")
        if diff["removed"]:
            click.echo(f"\nRemoved from org ({len(diff['removed'])}):")
            for name in sorted(diff["removed"]):
                click.echo(f"  - {name}")
        if not diff["new"] and not diff["removed"]:
            click.echo("\nNo differences from INVENTORY.md")


if __name__ == "__main__":
    main()
