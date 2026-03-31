"""Audit state cache: tracks which repos have been audited, staleness detection."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from . import config


def _load_state() -> dict:
    if config.AUDIT_STATE_PATH.is_file():
        return json.loads(config.AUDIT_STATE_PATH.read_text())
    return {"repos": {}}


def _save_state(state: dict) -> None:
    config.AUDIT_STATE_PATH.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n"
    )


def prompt_hash(prompt_content: str) -> str:
    """SHA-256 hash of prompt content, truncated to 12 hex chars."""
    return hashlib.sha256(prompt_content.encode()).hexdigest()[:12]


def check_staleness(
    repo_name: str,
    head_sha: str,
    current_prompt_hash: str,
) -> str:
    """Check if a repo needs re-auditing.

    Returns: 'current', 'stale', or 'never-audited'.
    """
    state = _load_state()
    entry = state.get("repos", {}).get(repo_name)

    if entry is None:
        return "never-audited"

    sha_match = entry.get("last_audit_sha") == head_sha
    prompt_match = entry.get("prompt_version_hash") == current_prompt_hash

    if sha_match and prompt_match:
        return "current"
    return "stale"


def record_audit(
    repo_name: str,
    commit_sha: str,
    prompt_name: str,
    prompt_hash_val: str,
    model: str,
) -> None:
    """Record a completed audit in the state file."""
    state = _load_state()
    state["repos"][repo_name] = {
        "last_audit_sha": commit_sha,
        "last_audit_date": datetime.now(timezone.utc).isoformat(),
        "prompt_version_hash": prompt_hash_val,
        "prompt_name": prompt_name,
        "model": model,
        "status": "current",
    }
    _save_state(state)


def get_state() -> dict:
    """Return the full audit state."""
    return _load_state()
