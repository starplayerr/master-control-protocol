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
import tempfile
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


# ── Normalisation ────────────────────────────────────────────────────────────


def _normalize_cell(s: str) -> str:
    """Strip whitespace and outer **bold** markers from table cells."""
    if not s:
        return ""
    t = s.strip()
    while len(t) >= 4 and t.startswith("**") and t.endswith("**"):
        t = t[2:-2].strip()
    return t


# ── Section title aliases (must match ## heading text after strip) ───────────

# Order matters: first match wins.
_SECTION_IDENTITY = (
    "Identity",
    "Repository identity",
    "Repository Identity",
)
_SECTION_TECH = ("Tech Stack", "Technology stack", "Tech stack")
_SECTION_PACKAGE = ("Package Details", "Package details")
_SECTION_DEPLOYMENT = ("Deployment",)

_SECTION_ARTIFACTS = ("Artifacts Produced", "Artifacts", "Build artifacts")
_SECTION_OUTBOUND = (
    "Outbound (what this repo depends on)",
    "Outbound dependencies",
    "Dependencies (outbound)",
    "Dependencies",
)
_SECTION_INBOUND = (
    "Inbound (what depends on this repo)",
    "Inbound dependencies",
    "Dependents",
)
_SECTION_CONFIG = (
    "Config / Sources of Truth",
    "Configuration",
    "Config / Source of Truth",
    "Sources of Truth",
    "Config",
)
_SECTION_API = ("API Surface", "API surface", "APIs")
_SECTION_SECRETS = (
    "Secrets and Auth",
    "Secrets & Auth",
    "Secrets",
    "Secrets and authentication",
)


def _rows_for_section(
    section_tables: dict[str, list[dict]], titles: tuple[str, ...]
) -> list[dict]:
    """Return rows from the first section whose heading is in titles."""
    for title in titles:
        if title in section_tables:
            return section_tables[title]
    return []


# ── Key-value table extraction ───────────────────────────────────────────────

# Field label -> AuditFacts attribute (Identity, Tech, Package, Deployment).
# Includes alternate wordings / v1-style labels for the same semantic field.
_IDENTITY_MAP = {
    "Repo name": "repo_name",
    "Repository": "repo_name",
    "GitHub URL": "github_url",
    "Repo": "github_url",
    "URL": "github_url",
    "Owner(s)": "owners",
    "Owners": "owners",
    "Prod status": "prod_status",
    "Production status": "prod_status",
    "Purpose": "purpose",
}

_TECH_MAP = {
    "Language(s)": "languages",
    "Languages": "languages",
    "Framework(s)": "frameworks",
    "Frameworks": "frameworks",
    "Build tool(s)": "build_tools",
    "Build tools": "build_tools",
    "Runtime": "runtime",
}

_PKG_MAP = {
    "Package name": "name",
    "Name": "name",
    "Registry": "registry",
    "Current version": "version",
    "Version": "version",
    "Version strategy": "version_strategy",
    "Known consumers": "consumers",
    "Consumers": "consumers",
    "Breaking change policy": "breaking_change_policy",
}

_DEPLOY_MAP = {
    "CI system": "ci",
    "CI": "ci",
    "CD system": "cd",
    "CD": "cd",
    "Target environment(s)": "targets",
    "Targets": "targets",
    "Pipeline file(s)": "pipeline_files",
    "Pipeline files": "pipeline_files",
}


def _extract_kv(rows: list[dict], mapping: dict[str, str]) -> dict:
    """Extract values from a Field|Value or Dimension|Value table."""
    result: dict = {}
    for row in rows:
        label = _normalize_cell(row.get("Field") or row.get("Dimension") or "")
        value = _normalize_cell(
            row.get("Value")
            or row.get("Details")
            or row.get("Description")
            or row.get("Current value")
            or ""
        )
        attr = mapping.get(label)
        if attr:
            result[attr] = value
    return result


def _row_pick(row: dict, *keys: str) -> str:
    """First non-empty normalized cell among alternate column names."""
    for k in keys:
        v = _normalize_cell(row.get(k, ""))
        if v:
            return v
    return ""


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
            gaps.append(_normalize_cell(stripped[2:]))
    return gaps


def _extract_purpose_prose(lines: list[str], max_chars: int = 500) -> str:
    """If Identity has no Purpose row, use a short prose paragraph under ## Identity."""
    in_identity = False
    parts: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("## "):
            if in_identity:
                break
            if s == "## Identity" or s.startswith("## Identity "):
                in_identity = True
            continue
        if not in_identity:
            continue
        if s.startswith("|"):
            continue
        if s.startswith("#"):
            break
        if s.startswith("- ") or s.startswith("* "):
            continue
        if s:
            parts.append(s)
    text = " ".join(parts).strip()
    if not text or len(text) > max_chars:
        return ""
    return text


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

    try:
        source_rel = str(audit_path.relative_to(config.MCP_ROOT))
    except ValueError:
        source_rel = str(audit_path)

    facts = AuditFacts(
        source_file=source_rel,
        last_updated=str(post.metadata.get("last_updated", "")),
    )

    section_tables: dict[str, list[dict]] = {}
    for t in tables:
        section_tables.setdefault(t["section"], []).extend(t["rows"])

    # Key-value sections (first matching section title)
    id_rows = _rows_for_section(section_tables, _SECTION_IDENTITY)
    if id_rows:
        facts.identity = Identity(**_extract_kv(id_rows, _IDENTITY_MAP))

    tech_rows = _rows_for_section(section_tables, _SECTION_TECH)
    if tech_rows:
        facts.tech_stack = TechStack(**_extract_kv(tech_rows, _TECH_MAP))

    pkg_rows = _rows_for_section(section_tables, _SECTION_PACKAGE)
    if pkg_rows:
        facts.package = PackageInfo(**_extract_kv(pkg_rows, _PKG_MAP))

    dep_rows = _rows_for_section(section_tables, _SECTION_DEPLOYMENT)
    if dep_rows:
        facts.deployment = Deployment(**_extract_kv(dep_rows, _DEPLOY_MAP))

    # Fallbacks: repo name from filename; purpose from prose under Identity
    if not facts.identity.repo_name:
        facts.identity.repo_name = audit_path.stem
    if not facts.identity.purpose:
        prose = _extract_purpose_prose(lines)
        if prose:
            facts.identity.purpose = prose

    # Row-list sections
    for t in tables:
        sec = t["section"]
        rows = t["rows"]
        if sec in _SECTION_ARTIFACTS:
            for row in rows:
                facts.artifacts.append(
                    {
                        "name": _row_pick(
                            row, "Artifact", "Name", "Package", "Output"
                        ),
                        "type": _row_pick(row, "Type", "Kind"),
                        "registry": _row_pick(row, "Registry", "Location"),
                        "destination": _row_pick(
                            row, "Destination", "Target", "Published to"
                        ),
                    }
                )
        elif sec in _SECTION_OUTBOUND:
            for row in rows:
                facts.outbound_deps.append(
                    {
                        "dependency": _row_pick(
                            row, "Dependency", "Name", "Package", "Resource"
                        ),
                        "type": _row_pick(row, "Type", "Kind"),
                        "notes": _row_pick(row, "Notes", "Note", "Description"),
                    }
                )
        elif sec in _SECTION_INBOUND:
            for row in rows:
                facts.inbound_deps.append(
                    {
                        "consumer": _row_pick(
                            row, "Consumer", "Name", "Dependent", "Client"
                        ),
                        "type": _row_pick(row, "Type", "Kind"),
                        "notes": _row_pick(row, "Notes", "Note", "Description"),
                    }
                )
        elif sec in _SECTION_CONFIG:
            for row in rows:
                facts.configs.append(
                    {
                        "config": _row_pick(
                            row,
                            "Config",
                            "Configuration",
                            "Key",
                            "Setting",
                            "Dimension",
                        ),
                        "source": _row_pick(
                            row, "Source", "Location", "Value", "Where"
                        ),
                        "notes": _row_pick(row, "Notes", "Note", "Description"),
                    }
                )
        elif sec in _SECTION_API:
            for row in rows:
                facts.api_surface.append(
                    {
                        "endpoint": _row_pick(
                            row,
                            "Endpoint / Interface",
                            "Endpoint",
                            "Interface",
                            "API",
                            "Path",
                        ),
                        "port": _row_pick(row, "Port"),
                        "protocol": _row_pick(row, "Protocol"),
                        "auth": _row_pick(row, "Auth", "Authentication"),
                        "notes": _row_pick(row, "Notes", "Note", "Description"),
                    }
                )
        elif sec in _SECTION_SECRETS:
            for row in rows:
                facts.secrets.append(
                    {
                        "name": _row_pick(
                            row,
                            "Secret / Credential",
                            "Secret",
                            "Credential",
                            "Name",
                        ),
                        "source": _row_pick(row, "Source", "Location"),
                        "usage": _row_pick(
                            row, "Used For", "Usage", "Purpose", "Notes"
                        ),
                    }
                )

    facts.known_gaps = _extract_known_gaps(lines)

    return facts


# ── Cache layer ────────────────────────────────────────────────────────────────


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


def _self_check() -> None:
    """Minimal regression checks for alternate markdown formats."""
    sample = """---
title: "Audit: demo"
last_updated: 2026-01-01
---
## Identity

Short purpose line for testing prose fallback.

| Dimension | Value |
| --- | --- |
| **Repo** | https://github.com/org/demo |
| Owners | **Jane Doe** |

## Dependencies

| Name | Type | Notes |
| --- | --- | --- |
| libfoo | library | ok |

## Config

| Key | Source |
| --- | --- |
| app.yaml | repo root |
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(sample)
        path = Path(f.name)
    try:
        facts = extract_facts(path)
        assert facts.identity.github_url == "https://github.com/org/demo", (
            facts.identity.github_url
        )
        assert facts.identity.owners == "Jane Doe", facts.identity.owners
        assert (
            facts.identity.purpose
            == "Short purpose line for testing prose fallback."
        ), facts.identity.purpose
        assert len(facts.outbound_deps) == 1, facts.outbound_deps
        assert facts.outbound_deps[0]["dependency"] == "libfoo"
        assert len(facts.configs) == 1, facts.configs
        # Repo name from filename when table has no Repo name row
        assert facts.identity.repo_name == path.stem
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    _self_check()
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
