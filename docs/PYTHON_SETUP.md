# TwinShip Ontology - Python Environment Setup

This project uses **[uv](https://github.com/astral-sh/uv)** for fast, modern Python package management.

**Minimum Python Version**: 3.9+ (required by rdflib dependency)

## Why uv?

- ⚡ **10-100x faster** than pip
- 🔒 **Reliable** - deterministic dependency resolution
- 🎯 **Simple** - single tool for venvs and packages
- 🚀 **Modern** - supports pyproject.toml natively
- 🔄 **Compatible** - works with existing pip/requirements.txt

## Quick Start

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Or with pip
pip install uv
```

### Install Dependencies

```bash
# Install all dependencies (creates venv automatically)
uv sync

# This is equivalent to:
#   python -m venv .venv
#   source .venv/bin/activate
#   pip install -r scripts/requirements.txt
# But MUCH faster!
```

### Activate Environment

```bash
# Activate the virtual environment
source .venv/bin/activate  # macOS/Linux
# Or: .venv\Scripts\activate  # Windows

# Or use uv run (no activation needed)
uv run python scripts/merge_modules.py --help
```

## Common Commands

```bash
# Install dependencies
uv sync

# Add a new package
uv add <package-name>

# Add a dev dependency (goes to [dependency-groups] dev)
uv add --dev <package-name>

# Run the website build (a shell script that calls uv itself)
./scripts/generate_website.sh

# Update all dependencies
uv sync --upgrade

# Show installed packages
uv pip list
```

## Project Structure

- **pyproject.toml** - Modern Python project configuration (uv native)
- **uv.lock** - Locked dependency versions (tracked; CI installs with `uv sync --frozen`)
- **scripts/requirements.txt** - Legacy format (for compatibility)
- **.venv/** - Virtual environment (created by `uv sync`)

## For Traditional pip Users

If you prefer traditional pip, you can still use:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

This installs what the scripts need. For the development tools (pytest, black, ruff, pyshacl), also run `pip install --group dev` (pip 25.1 or later).

But we **strongly recommend uv** for better performance and reliability.

## Troubleshooting

### uv not found after installation

```bash
# Add to PATH (usually done automatically)
export PATH="$HOME/.local/bin:$PATH"

# Add to ~/.zshrc or ~/.bashrc for persistence
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

### Want to use system Python?

```bash
# uv uses the system Python by default
# To specify a version:
uv venv --python 3.11
uv sync
```

### Lock file issues?

```bash
# Regenerate lock file
uv lock
uv sync
# Commit the updated uv.lock; CI uses uv sync --frozen and fails if it is out of date
```

## Learn More

- uv Documentation: https://docs.astral.sh/uv/
- uv GitHub: https://github.com/astral-sh/uv
- Python Packaging Guide: https://packaging.python.org/

---

**Recommended**: Use `uv sync` for all dependency management in this project.
