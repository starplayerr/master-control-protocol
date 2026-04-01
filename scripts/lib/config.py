"""Shared configuration: paths, env vars, constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────

MCP_ROOT = Path(os.getenv("MCP_ROOT", Path(__file__).resolve().parents[2]))
AUDITS_DIR = MCP_ROOT / "audits"
PROMPTS_DIR = MCP_ROOT / "prompts"
INVENTORY_PATH = MCP_ROOT / "INVENTORY.md"
PRIORITY_CLONES_PATH = MCP_ROOT / "PRIORITY_CLONES.md"
AUDIT_STATE_PATH = MCP_ROOT / "audit-state.json"
DISCOVERED_PATH = MCP_ROOT / "discovered.json"
MAPS_DIR = MCP_ROOT / "maps"
MAPS_DATA_DIR = MCP_ROOT / "maps" / "data"
FACTS_CACHE_DIR = MCP_ROOT / "facts-cache"
DIAGRAMS_DIR = MCP_ROOT / "diagrams"
CLONES_DIR = MCP_ROOT / ".clones"

# ── Secrets ────────────────────────────────────────────────────────────────

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ── Defaults ───────────────────────────────────────────────────────────────

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
}
DEFAULT_MAX_OUTPUT_TOKENS = 8192
DEFAULT_CONTEXT_BUDGET = 100_000  # characters
DEFAULT_CONCURRENCY = 3

# ── Git history analysis ──────────────────────────────────────────────────

DEFAULT_HISTORY_MONTHS = 6
DEFAULT_COUPLING_WINDOW_HOURS = 48

# ── File reading ───────────────────────────────────────────────────────────

MAX_SINGLE_FILE_CHARS = 10_000

SKIP_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Pipfile.lock",
    "poetry.lock",
    "go.sum",
    "composer.lock",
    "Gemfile.lock",
    "Cargo.lock",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".bz2", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".pyc", ".pyo", ".class", ".o", ".so", ".dylib", ".dll",
    ".exe", ".bin",
}

# Priority-ordered list of config files the context gatherer looks for.
CONFIG_FILES = [
    "README.md", "README", "readme.md",
    "package.json", "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg",
    "go.mod", "Cargo.toml", "rust-toolchain.toml", "dist-workspace.toml",
    "Gemfile", "build.gradle", "pom.xml",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "Makefile",
    "Jenkinsfile",
    "jules.yaml", "jib.yaml",
    "spinnaker-trigger.yaml", "triggerable.yaml",
    "chart.yaml", "Chart.yaml", "values.yaml",
    "main.tf", "variables.tf", "outputs.tf",
    "kustomization.yaml",
    "buildspec.yml",
    "Procfile",
]

CI_GLOBS = [
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    ".circleci/config.yml",
    ".gitlab-ci.yml",
    "Jenkinsfile",
]

ENTRY_POINT_PATTERNS = [
    "main.go", "cmd/*/main.go",
    "app.py", "main.py", "manage.py", "wsgi.py",
    "index.ts", "index.js", "src/index.ts", "src/index.js",
    "src/main.rs", "src/lib.rs",
    "crates/*/Cargo.toml", "crates/*/src/lib.rs", "crates/*/src/main.rs",
]
