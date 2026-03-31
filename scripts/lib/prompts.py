"""Prompt loading and auto-selection based on repo file signatures."""

from __future__ import annotations

import json
from pathlib import Path

from . import config


def load_prompt(name: str) -> str:
    """Load a prompt file by name (without .md extension)."""
    path = config.PROMPTS_DIR / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text()


def list_prompts() -> list[str]:
    """List available prompt names."""
    return [p.stem for p in config.PROMPTS_DIR.glob("*.md")]


def detect_repo_type(repo_path: Path) -> str:
    """Auto-detect repo type from file signatures. Returns a prompt name."""

    has_tf = any(repo_path.glob("**/*.tf"))
    has_helm = (repo_path / "Chart.yaml").is_file() or (repo_path / "chart.yaml").is_file()
    has_kustomize = (repo_path / "kustomization.yaml").is_file()
    has_dockerfile = (repo_path / "Dockerfile").is_file()
    has_cargo_toml = (repo_path / "Cargo.toml").is_file()
    pkg_json = repo_path / "package.json"
    has_pkg_json = pkg_json.is_file()

    # Infrastructure: Terraform, Helm, or Kustomize
    if has_tf or has_helm or has_kustomize:
        return "infrastructure"

    # Rust: Cargo.toml present — CLI tool or library, never "service"
    if has_cargo_toml:
        return "library"

    # Frontend: package.json with a UI framework dependency
    if has_pkg_json:
        try:
            pkg = json.loads(pkg_json.read_text())
            all_deps = {
                *pkg.get("dependencies", {}).keys(),
                *pkg.get("devDependencies", {}).keys(),
            }
            ui_frameworks = {"react", "vue", "angular", "@angular/core", "next", "nuxt", "svelte"}
            if all_deps & ui_frameworks:
                return "frontend"
            # Library: package.json with main/bin but no UI framework
            if "main" in pkg or "bin" in pkg or "exports" in pkg:
                return "library"
        except (json.JSONDecodeError, OSError):
            pass

    # Library: Python package with setup.py/pyproject.toml publishing indicators
    pyproject = repo_path / "pyproject.toml"
    setup_py = repo_path / "setup.py"
    if pyproject.is_file() or setup_py.is_file():
        # Check for publishing-related config
        if pyproject.is_file():
            content = pyproject.read_text()
            if "[project]" in content or "[tool.poetry]" in content:
                if has_dockerfile:
                    return "service"
                return "library"

    # Go library: go.mod without main.go or Dockerfile
    go_mod = repo_path / "go.mod"
    main_go = repo_path / "main.go"
    cmd_dir = repo_path / "cmd"
    if go_mod.is_file() and not main_go.is_file() and not cmd_dir.is_dir() and not has_dockerfile:
        return "library"

    # Service: has a Dockerfile with entry points suggesting a running service
    if has_dockerfile:
        return "service"

    return "default"


def select_prompt(repo_path: Path, override: str | None = None) -> tuple[str, str]:
    """Select and load a prompt. Returns (prompt_name, prompt_content)."""
    name = override or detect_repo_type(repo_path)
    # Fall back to default if the detected type doesn't have a prompt file
    try:
        content = load_prompt(name)
    except FileNotFoundError:
        name = "default"
        content = load_prompt(name)
    return name, content
