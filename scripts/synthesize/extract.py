#!/usr/bin/env python3
"""Shared extraction layer for the synthesis engine.

Loads audit reports from audits/, parses frontmatter and markdown tables,
and produces normalised AuditFacts dataclass instances. Results are cached
in facts-cache/ keyed by repo name + audit last_updated date.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config
from lib.markdown import parse_md_tables_from_lines


# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class Identity:
    repo_name: str = ""
    github_url: str = ""
    owners: str = ""
    prod_status: str = ""
    purpose: str = ""


@dataclass
class TechStack:
    languages: str = ""
    frameworks: str = ""
    build_tools: str = ""
    runtime: str = ""


@dataclass
class PackageInfo:
    name: str = ""
    registry: str = ""
    version: str = ""
    version_strategy: str = ""
    consumers: str = ""
    breaking_change_policy: str = ""


@dataclass
class Deployment:
    ci: str = ""
    cd: str = ""
    targets: str = ""
    pipeline_files: str = ""


@dataclass
class AuditFacts:
    source_file: str = ""
    last_updated: str = ""
    identity: Identity = field(default_factory=Identity)
    tech_stack: TechStack = field(default_factory=TechStack)
    artifacts: list[dict] = field(default_factory=list)
    package: PackageInfo = field(default_factory=PackageInfo)
    deployment: Deployment = field(default_factory=Deployment)
    outbound_deps: list[dict] = field(default_factory=list)
    inbound_deps: list[dict] = field(default_factory=list)
    configs: list[dict] = field(default_factory=list)
    api_surface: list[dict] = field(default_factory=list)
    secrets: list[dict] = field(default_factory=list)
    known_gaps: list[str] = field(default_factory=list)


# ── Key-value table extraction ───────────────────────────────────────────────

# These sections use a two-column Field | Value layout
_KV_SECTIONS = {"Identity", "Tech Stack", "Package Details", "Deployment"}

_IDENTITY_MAP = {
    "Repo name": "repo_name",
    "GitHub URL": "github_url",
    "Owner(s)": "owners",
    "Prod status": "prod_status",
    "Purpose": "purpose",
}

_TECH_MAP = {
    "Language(s)": "languages",
    "Framework(s)": "frameworks",
    "Build tool(s)": "build_tools",
    "Runtime": "runtime",
}

_PKG_MAP = {
    "Package name": "name",
    "Registry": "registry",
    "Current version": "version",
    "Version strategy": "version_strategy",
    "Known consumers": "consumers",
    "Breaking change policy": "breaking_change_policy",
}

_DEPLOY_MAP = {
    "CI system": "ci",
    "CD system": "cd",
    "Target environment(s)": "targets",
    "Pipeline file(s)": "pipeline_files",
}


def _extract_kv(rows: list[dict], mapping: dict) -> dict:
    """Extract values from a Field|Value table using a mapping."""
    result = {}
    for row in rows:
        field_name = row.get("Field", "")
        value = row.get("Value", "")
        attr = mapping.get(field_name)
        if attr:
            result[attr] = value
    return result


# ── List-section extraction ──────────────────────────────────────────────────


def _extract_known_gaps(lines: list[str]) -> list[str]:
    """Pull bullet items from the Known Gaps section."""
    gaps: list[str] = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Known Gaps"):
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if in_section and stripped.startswith("- "):
            gaps.append(stripped[2:].strip())
    return gaps


# ── Audit-meta HTML comment extraction ───────────────────────────────────────

_META_RE = re.compile(r"<!--\s*audit-meta\s*(.*?)-->", re.DOTALL)


def _parse_audit_meta(text: str) -> dict:
    """Parse the <!-- audit-meta ... --> HTML comment block."""
    m = _META_RE.search(text)
    if not m:
        return {}
    meta = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()
    return meta


# ── Main extraction ──────────────────────────────────────────────────────────


def extract_facts(audit_path: Path) -> AuditFacts:
    """Parse a single audit markdown file into structured AuditFacts."""
    post = frontmatter.load(str(audit_path))
    text = audit_path.read_text()
    lines = text.splitlines()
    tables = parse_md_tables_from_lines(lines)

    facts = AuditFacts(
        source_file=str(audit_path.relative_to(config.MCP_ROOT)),
        last_updated=str(post.metadata.get("last_updated", "")),
    )

    section_tables: dict[str, list[dict]] = {}
    for t in tables:
        section_tables.setdefault(t["section"], []).extend(t["rows"])

    # Key-value sections
    if "Identity" in section_tables:
        facts.identity = Identity(**_extract_kv(section_tables["Identity"], _IDENTITY_MAP))
    if "Tech Stack" in section_tables:
        facts.tech_stack = TechStack(**_extract_kv(section_tables["Tech Stack"], _TECH_MAP))
    if "Package Details" in section_tables:
        facts.package = PackageInfo(**_extract_kv(section_tables["Package Details"], _PKG_MAP))
    if "Deployment" in section_tables:
        facts.deployment = Deployment(**_extract_kv(section_tables["Deployment"], _DEPLOY_MAP))

    # Row-list sections
    for t in tables:
        sec = t["section"]
        if sec == "Artifacts Produced":
            for row in t["rows"]:
                facts.artifacts.append({
                    "name": row.get("Artifact", ""),
                    "type": row.get("Type", ""),
                    "registry": row.get("Registry", ""),
                    "destination": row.get("Destination", ""),
                })
        elif sec == "Outbound (what this repo depends on)":
            for row in t["rows"]:
                facts.outbound_deps.append({
                    "dependency": row.get("Dependency", ""),
                    "type": row.get("Type", ""),
                    "notes": row.get("Notes", ""),
                })
        elif sec == "Inbound (what depends on this repo)":
            for row in t["rows"]:
                facts.inbound_deps.append({
                    "consumer": row.get("Consumer", ""),
                    "type": row.get("Type", ""),
                    "notes": row.get("Notes", ""),
                })
        elif sec == "Config / Sources of Truth":
            for row in t["rows"]:
                facts.configs.append({
                    "config": row.get("Config", ""),
                    "source": row.get("Source", ""),
                    "notes": row.get("Notes", ""),
                })
        elif sec == "API Surface":
            for row in t["rows"]:
                facts.api_surface.append({
                    "endpoint": row.get("Endpoint / Interface", ""),
                    "port": row.get("Port", ""),
                    "protocol": row.get("Protocol", ""),
                    "auth": row.get("Auth", ""),
                    "notes": row.get("Notes", ""),
                })
        elif sec == "Secrets and Auth":
            for row in t["rows"]:
                facts.secrets.append({
                    "name": row.get("Secret / Credential", ""),
                    "source": row.get("Source", ""),
                    "usage": row.get("Used For", ""),
                })

    facts.known_gaps = _extract_known_gaps(lines)

    return facts


# ── Cache layer ──────────────────────────────────────────────────────────────


def _cache_path(repo_name: str) -> Path:
    return config.FACTS_CACHE_DIR / f"{repo_name}.json"


def _cache_valid(repo_name: str, last_updated: str) -> bool:
    cp = _cache_path(repo_name)
    if not cp.is_file():
        return False
    try:
        cached = json.loads(cp.read_text())
        return cached.get("last_updated") == last_updated
    except (json.JSONDecodeError, OSError):
        return False


def _write_cache(facts: AuditFacts) -> None:
    config.FACTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(facts.identity.repo_name).write_text(
        json.dumps(asdict(facts), indent=2) + "\n"
    )


def _read_cache(repo_name: str) -> AuditFacts:
    data = json.loads(_cache_path(repo_name).read_text())
    return _dict_to_facts(data)


def _dict_to_facts(d: dict) -> AuditFacts:
    """Reconstruct an AuditFacts from a serialised dict."""
    return AuditFacts(
        source_file=d.get("source_file", ""),
        last_updated=d.get("last_updated", ""),
        identity=Identity(**d.get("identity", {})),
        tech_stack=TechStack(**d.get("tech_stack", {})),
        artifacts=d.get("artifacts", []),
        package=PackageInfo(**d.get("package", {})),
        deployment=Deployment(**d.get("deployment", {})),
        outbound_deps=d.get("outbound_deps", []),
        inbound_deps=d.get("inbound_deps", []),
        configs=d.get("configs", []),
        api_surface=d.get("api_surface", []),
        secrets=d.get("secrets", []),
        known_gaps=d.get("known_gaps", []),
    )


# ── Public API ───────────────────────────────────────────────────────────────


def load_all_audits(use_cache: bool = True) -> dict[str, AuditFacts]:
    """Load and extract facts from every audit in audits/.

    Returns a dict keyed by repo name.  Skips the _meta/ subdirectory.
    """
    results: dict[str, AuditFacts] = {}

    for md in sorted(config.AUDITS_DIR.glob("*.md")):
        if md.name.startswith("_"):
            continue

        post = frontmatter.load(str(md))
        last_updated = str(post.metadata.get("last_updated", ""))

        # Derive repo name from filename (e.g. ruff-vscode.md -> ruff-vscode)
        repo_name = md.stem

        if use_cache and _cache_valid(repo_name, last_updated):
            results[repo_name] = _read_cache(repo_name)
            continue

        facts = extract_facts(md)
        _write_cache(facts)
        results[repo_name] = facts

    return results


if __name__ == "__main__":
    all_facts = load_all_audits(use_cache=False)
    print(f"Extracted facts from {len(all_facts)} audits:\n")
    for name, facts in all_facts.items():
        n_deps = len(facts.outbound_deps)
        n_in = len(facts.inbound_deps)
        n_cfg = len(facts.configs)
        n_art = len(facts.artifacts)
        print(
            f"  {name}: "
            f"v{facts.package.version or '?'}, "
            f"{n_deps} outbound deps, {n_in} inbound, "
            f"{n_cfg} configs, {n_art} artifacts, "
            f"{len(facts.known_gaps)} gaps"
        )
