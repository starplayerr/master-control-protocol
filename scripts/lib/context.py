"""Repo context gathering: clone, tree, file reading with budget."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from pathspec import PathSpec

from . import config


@dataclass
class GatheredContext:
    """Result of gathering context from a repo."""

    repo_path: Path
    tree: str
    files: dict[str, str]  # relative path -> content
    included: list[str] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    total_chars: int = 0

    def to_prompt_string(self) -> str:
        parts = [f"## Directory Tree\n\n```\n{self.tree}\n```"]
        for relpath, content in self.files.items():
            parts.append(f"\n## File: {relpath}\n\n```\n{content}\n```")
        return "\n".join(parts)


def shallow_clone(repo_url: str, branch: str | None = None) -> Path:
    """Shallow-clone a repo into a temp directory. Returns the path."""
    tmpdir = Path(tempfile.mkdtemp(prefix="mcp-audit-"))
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd += ["--branch", branch]
    cmd += [repo_url, str(tmpdir / "repo")]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return tmpdir / "repo"


def cleanup_clone(tmpdir: Path) -> None:
    """Remove a cloned temp directory."""
    root = tmpdir.parent if tmpdir.name == "repo" else tmpdir
    shutil.rmtree(root, ignore_errors=True)


def _load_mcpignore_spec(repo_root: Path) -> PathSpec | None:
    """Merge patterns from MCP_ROOT/.mcpignore and repo_root/.mcpignore (gitwildmatch)."""
    paths = [config.MCP_ROOT / ".mcpignore", repo_root / ".mcpignore"]
    lines: list[str] = []
    for p in paths:
        if not p.is_file():
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        for raw in text.splitlines():
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            lines.append(stripped)
    if not lines:
        return None
    return PathSpec.from_lines("gitwildmatch", lines)


def _mcp_excluded(spec: PathSpec | None, rel_posix: str, *, is_dir: bool) -> bool:
    """True if path is excluded by .mcpignore (never read or sent to LLM)."""
    if spec is None:
        return False
    norm = rel_posix.replace("\\", "/")
    if spec.match_file(norm):
        return True
    if is_dir:
        base = norm.rstrip("/")
        if base and spec.match_file(base + "/"):
            return True
    return False


def _rel_posix(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.name


def generate_tree(
    repo_path: Path,
    max_depth: int = 3,
    mcpignore_spec: PathSpec | None = None,
) -> str:
    """Generate a directory tree string, limited to max_depth levels."""
    lines: list[str] = []
    root = repo_path.resolve()

    def _walk(current: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(current.iterdir(), key=lambda e: (not e.is_dir(), e.name))
        except PermissionError:
            return
        dirs = [e for e in entries if e.is_dir() and not e.name.startswith(".")]
        files = [e for e in entries if e.is_file()]
        items: list[Path] = []
        for entry in dirs + files:
            rel = _rel_posix(root, entry)
            if _mcp_excluded(mcpignore_spec, rel, is_dir=entry.is_dir()):
                continue
            items.append(entry)
        for i, entry in enumerate(items):
            connector = "└── " if i == len(items) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir() and not entry.name.startswith("."):
                extension = "    " if i == len(items) - 1 else "│   "
                _walk(entry, prefix + extension, depth + 1)

    lines.append(root.name + "/")
    _walk(root, "", 1)
    return "\n".join(lines)


def _is_binary(path: Path) -> bool:
    return path.suffix.lower() in config.BINARY_EXTENSIONS


def _should_skip(path: Path) -> bool:
    return path.name in config.SKIP_FILENAMES or _is_binary(path)


def _find_files_by_patterns(repo_path: Path, patterns: list[str]) -> list[Path]:
    """Find files matching glob-like patterns relative to repo root."""
    found: list[Path] = []
    for pattern in patterns:
        if "*" in pattern:
            found.extend(repo_path.glob(pattern))
        else:
            candidate = repo_path / pattern
            if candidate.is_file():
                found.append(candidate)
    return found


def _read_file_budgeted(path: Path, max_chars: int) -> str:
    """Read a file, truncating if over budget."""
    try:
        text = path.read_text(errors="replace")
    except (OSError, UnicodeDecodeError):
        return ""
    if len(text) > max_chars:
        return text[:max_chars] + f"\n\n... [truncated at {max_chars:,} chars]"
    return text


def gather_context(
    repo_path: Path,
    budget: int = config.DEFAULT_CONTEXT_BUDGET,
) -> GatheredContext:
    """Gather repo context files within a character budget."""
    repo_root = repo_path.resolve()
    spec = _load_mcpignore_spec(repo_root)
    tree = generate_tree(repo_path, mcpignore_spec=spec)
    ctx = GatheredContext(repo_path=repo_path, tree=tree, files={})
    remaining = budget - len(ctx.tree)

    # Build prioritized file list: config files, then CI, then entry points
    priority_files: list[Path] = []
    priority_files.extend(_find_files_by_patterns(repo_path, config.CONFIG_FILES))
    priority_files.extend(_find_files_by_patterns(repo_path, config.CI_GLOBS))
    priority_files.extend(_find_files_by_patterns(repo_path, config.ENTRY_POINT_PATTERNS))

    # Also look for config/ and deploy/ directories
    for subdir_name in ("config", "deploy", "deployment", "infra"):
        subdir = repo_path / subdir_name
        if subdir.is_dir():
            for child in sorted(subdir.iterdir()):
                if child.is_file() and not _should_skip(child):
                    priority_files.append(child)

    # Deduplicate while preserving order
    seen: set[Path] = set()
    unique_files: list[Path] = []
    for f in priority_files:
        resolved = f.resolve()
        if resolved not in seen and f.is_file():
            seen.add(resolved)
            unique_files.append(f)

    for fpath in unique_files:
        rel = _rel_posix(repo_root, fpath)
        if _mcp_excluded(spec, rel, is_dir=False):
            ctx.excluded.append(rel)
            continue
        if _should_skip(fpath):
            ctx.excluded.append(rel)
            continue

        content = _read_file_budgeted(fpath, config.MAX_SINGLE_FILE_CHARS)
        if not content:
            continue

        if len(content) > remaining:
            ctx.excluded.append(rel)
            continue

        ctx.files[rel] = content
        ctx.included.append(rel)
        remaining -= len(content)
        ctx.total_chars += len(content)

    ctx.total_chars += len(ctx.tree)
    return ctx


def get_head_sha(repo_path: Path) -> str:
    """Get the HEAD commit SHA of a cloned repo."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
