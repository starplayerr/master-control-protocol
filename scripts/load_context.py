"""Context budget loader: load MCP content into a token-budgeted context window."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import tiktoken

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "mcp-manifest.json"


def load_manifest() -> dict:
    if not MANIFEST_PATH.is_file():
        click.echo("Error: mcp-manifest.json not found.", err=True)
        sys.exit(1)
    return json.loads(MANIFEST_PATH.read_text())


def count_tokens(text: str, encoding: tiktoken.Encoding) -> int:
    return len(encoding.encode(text))


def format_file_block(rel_path: str, content: str) -> str:
    """Wrap file content in a labeled block for agent consumption."""
    separator = "=" * 60
    return f"\n{separator}\nFILE: {rel_path}\n{separator}\n\n{content}\n"


@click.command()
@click.option("--tokens", default=50000, type=int, help="Token budget (default: 50000).")
@click.option("--include-audits", is_flag=True, help="Include all audit files after manifest items.")
@click.option("--repo", multiple=True, help="Include audit for specific repo(s) by name.")
@click.option("--include-diagrams", is_flag=True, help="Include diagram files after maps.")
def main(tokens: int, include_audits: bool, repo: tuple[str, ...], include_diagrams: bool) -> None:
    """Load MCP content into a context window, respecting read order and token budget."""
    manifest = load_manifest()
    enc = tiktoken.encoding_for_model("gpt-4")  # cl100k_base

    budget = tokens
    used = 0
    parts: list[str] = []
    loaded_files: list[str] = []
    skipped_files: list[str] = []

    for entry in manifest["read_order"]:
        fpath = ROOT / entry["path"]
        if not fpath.is_file():
            continue

        content = fpath.read_text()
        block = format_file_block(entry["path"], content)
        cost = count_tokens(block, enc)

        if used + cost > budget:
            skipped_files.append(entry["path"])
            continue

        parts.append(block)
        used += cost
        loaded_files.append(entry["path"])

    if include_audits and used < budget:
        audits_dir = ROOT / manifest.get("audits_dir", "audits/")
        if audits_dir.is_dir():
            for audit_file in sorted(audits_dir.glob("*.md")):
                rel = str(audit_file.relative_to(ROOT))
                content = audit_file.read_text()
                block = format_file_block(rel, content)
                cost = count_tokens(block, enc)
                if used + cost > budget:
                    skipped_files.append(rel)
                    continue
                parts.append(block)
                used += cost
                loaded_files.append(rel)

    if repo and used < budget:
        audits_dir = ROOT / manifest.get("audits_dir", "audits/")
        for repo_name in repo:
            audit_file = audits_dir / f"{repo_name}.md"
            rel = str(audit_file.relative_to(ROOT))
            if rel in loaded_files:
                continue
            if not audit_file.is_file():
                click.echo(f"Warning: audit not found for '{repo_name}'", err=True)
                continue

            content = audit_file.read_text()
            block = format_file_block(rel, content)
            cost = count_tokens(block, enc)
            if used + cost > budget:
                skipped_files.append(rel)
                continue
            parts.append(block)
            used += cost
            loaded_files.append(rel)

    if include_diagrams and used < budget:
        diagrams_dir = ROOT / manifest.get("diagrams_dir", "diagrams/")
        if diagrams_dir.is_dir():
            for diagram_file in sorted(diagrams_dir.glob("*.md")):
                rel = str(diagram_file.relative_to(ROOT))
                content = diagram_file.read_text()
                block = format_file_block(rel, content)
                cost = count_tokens(block, enc)
                if used + cost > budget:
                    skipped_files.append(rel)
                    continue
                parts.append(block)
                used += cost
                loaded_files.append(rel)

    header = (
        f"# MCP Context Snapshot\n\n"
        f"Token budget: {budget:,} | Used: {used:,} | Remaining: {budget - used:,}\n"
        f"Files loaded: {len(loaded_files)}\n\n"
    )
    if skipped_files:
        header += f"Skipped (budget exceeded): {', '.join(skipped_files)}\n\n"

    output = header + "".join(parts)
    click.echo(output)

    click.echo(
        f"\n--- Loaded {len(loaded_files)} files, ~{used:,} tokens of {budget:,} budget ---",
        err=True,
    )


if __name__ == "__main__":
    main()
