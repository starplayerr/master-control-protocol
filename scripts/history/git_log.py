"""Clone management and structured git-log extraction.

Maintains bare blobless clones in .clones/ and extracts commit history
into typed Python dataclasses for the analysis pipeline.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import config


# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class FileChange:
    added: int
    deleted: int
    path: str


@dataclass
class CommitInfo:
    sha: str
    timestamp: datetime
    author_name: str
    author_email: str
    files_changed: list[FileChange] = field(default_factory=list)


@dataclass
class RepoHistory:
    repo_name: str
    default_branch: str
    commits: list[CommitInfo] = field(default_factory=list)


# ── Clone management ────────────────────────────────────────────────────────

COMMIT_SEP = "---COMMIT_SEP---"
LOG_FORMAT = f"{COMMIT_SEP}%n%H%n%aI%n%aN%n%aE"


def _run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result


def ensure_clone(repo_name: str, repo_url: str) -> Path:
    """Ensure a bare blobless clone exists and is up-to-date. Returns clone path."""
    config.CLONES_DIR.mkdir(parents=True, exist_ok=True)
    clone_path = config.CLONES_DIR / f"{repo_name}.git"

    if clone_path.exists():
        _run_git(["fetch", "--all", "--prune"], cwd=clone_path)
    else:
        result = _run_git([
            "clone", "--bare", "--filter=blob:none",
            repo_url, str(clone_path),
        ])
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to clone {repo_url}: {result.stderr.strip()}"
            )

    return clone_path


def load_discovered_repos() -> list[dict]:
    """Load repo metadata from discovered.json."""
    if not config.DISCOVERED_PATH.is_file():
        raise FileNotFoundError(
            f"discovered.json not found at {config.DISCOVERED_PATH}. "
            "Run scripts/discover.py first."
        )
    data = json.loads(config.DISCOVERED_PATH.read_text())
    return data.get("repos", [])


def get_audited_repo_names() -> set[str]:
    """Return the set of repo names that have been audited."""
    if not config.AUDIT_STATE_PATH.is_file():
        return set()
    data = json.loads(config.AUDIT_STATE_PATH.read_text())
    return set(data.get("repos", {}).keys())


# ── Log extraction ──────────────────────────────────────────────────────────


def _parse_numstat_line(line: str) -> FileChange | None:
    """Parse a single --numstat output line like '10\t5\tsrc/main.rs'."""
    parts = line.split("\t", 2)
    if len(parts) != 3:
        return None
    added_str, deleted_str, path = parts
    try:
        added = int(added_str) if added_str != "-" else 0
        deleted = int(deleted_str) if deleted_str != "-" else 0
    except ValueError:
        return None
    return FileChange(added=added, deleted=deleted, path=path)


def extract_history(
    clone_path: Path,
    branch: str,
    months: int = config.DEFAULT_HISTORY_MONTHS,
) -> list[CommitInfo]:
    """Extract structured commit history from a bare clone."""
    since_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
    since_str = since_date.strftime("%Y-%m-%d")

    result = _run_git([
        "log",
        f"--since={since_str}",
        f"--format={LOG_FORMAT}",
        "--numstat",
        branch,
    ], cwd=clone_path)

    if result.returncode != 0:
        # Try with origin/ prefix for bare repos
        result = _run_git([
            "log",
            f"--since={since_str}",
            f"--format={LOG_FORMAT}",
            "--numstat",
            f"origin/{branch}",
        ], cwd=clone_path)

    if result.returncode != 0:
        return []

    return _parse_log_output(result.stdout)


def _parse_log_output(raw: str) -> list[CommitInfo]:
    """Parse the combined --format + --numstat output into CommitInfo objects."""
    commits: list[CommitInfo] = []
    blocks = raw.split(COMMIT_SEP)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split("\n")
        if len(lines) < 4:
            continue

        sha = lines[0].strip()
        timestamp_str = lines[1].strip()
        author_name = lines[2].strip()
        author_email = lines[3].strip()

        if not sha or not timestamp_str:
            continue

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            continue

        files: list[FileChange] = []
        for line in lines[4:]:
            line = line.strip()
            if not line:
                continue
            fc = _parse_numstat_line(line)
            if fc:
                files.append(fc)

        commits.append(CommitInfo(
            sha=sha,
            timestamp=timestamp,
            author_name=author_name,
            author_email=author_email,
            files_changed=files,
        ))

    return commits


# ── High-level API ──────────────────────────────────────────────────────────


def fetch_all_histories(
    months: int = config.DEFAULT_HISTORY_MONTHS,
    only_audited: bool = True,
    verbose: bool = True,
) -> dict[str, RepoHistory]:
    """Clone/update all repos and extract their histories.

    If only_audited is True, limits to repos present in audit-state.json.
    Returns a dict keyed by repo name.
    """
    repos = load_discovered_repos()
    audited = get_audited_repo_names() if only_audited else None

    histories: dict[str, RepoHistory] = {}

    for repo_meta in repos:
        name = repo_meta["name"]
        if audited is not None and name not in audited:
            continue

        url = repo_meta["url"]
        branch = repo_meta.get("default_branch", "main")

        if verbose:
            print(f"  Fetching {name}...", end=" ", flush=True)

        try:
            clone_path = ensure_clone(name, url)
            commits = extract_history(clone_path, branch, months=months)
            histories[name] = RepoHistory(
                repo_name=name,
                default_branch=branch,
                commits=commits,
            )
            if verbose:
                print(f"{len(commits)} commits")
        except Exception as e:
            if verbose:
                print(f"FAILED: {e}")

    return histories


def normalise_author(name: str, email: str) -> str:
    """Produce a stable author key from name + email."""
    return email.lower().strip() if email else name.lower().strip()


def anonymise_author(key: str) -> str:
    """Replace an author key with a stable short hash."""
    import hashlib
    return "author_" + hashlib.sha256(key.encode()).hexdigest()[:6]
