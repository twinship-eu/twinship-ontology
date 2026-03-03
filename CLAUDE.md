# CLAUDE.md — AI Agent Context for TwinShip Ontology

## Project Overview

This is an **OWL ontology** for the TwinShip EU project — a digital twin ontology for maritime vessels. The primary artifacts are **Turtle (.ttl) ontology files**, not application code. Python scripts are build tooling that transforms, filters, and documents the ontology.

## Agent Workflow Requirements

### Planning and Confirmation

**ALWAYS follow this workflow for any non-trivial task:**

1. **Analyze the request** — Understand what the user wants to accomplish
2. **Create a detailed plan** — Break down the work into specific steps
3. **Present the plan to the user** — Clearly explain what will be modified/created
4. **Wait for confirmation** — Do NOT proceed until the user approves the plan
5. **Execute the plan** — Implement the changes as approved
6. **Report results** — Summarize what was done and which files were modified

**IMPORTANT:** Plans must NEVER include git operations (add/commit/push) as steps. Plans should focus only on the technical implementation. Always end with reporting results, not committing changes.

### Version Control Workflow

**NEVER include git operations in plans or automatically suggest them** unless explicitly requested by the user.

The user will decide when to:
- Stage changes (`git add`)
- Commit changes (`git commit`)
- Push to GitHub (`git push`)

**After completing implementation work:**
1. Report what files were modified
2. Summarize what was accomplished
3. **STOP** - Let the user review and test the changes
4. Wait for the user to explicitly request git operations

**Only perform git operations when:**
- The user explicitly asks to commit, push, or stage changes
- Creating a new branch when explicitly requested by the user

**Never say:** "Now let's commit these changes" or "Ready to commit" or include commit steps in plans.

### When to Skip Planning

You may skip the formal planning step for:
- Simple information queries (e.g., "what files are in this directory?")
- Reading/viewing files
- Searching for information
- Quick status checks

## Critical Design Decision: Restriction-Based Modeling

**NEVER add `rdfs:domain` or `rdfs:range` to source model files** (`model/*.ttl`, `model/modules/*.ttl`).

The ontology uses **OWL restrictions** (`owl:someValuesFrom`, `owl:allValuesFrom`) instead of `rdfs:domain`/`rdfs:range` to avoid unwanted inferences. Domain/range assertions exist **only** in auto-generated visualization files (`build/*-viz*.ttl`). The build scripts convert restrictions to domain/range automatically.

## Repository Structure

### Source files (version-controlled, manually edited)

- `model/twinship-base.ttl` — Foundation layer (base classes, properties)
- `model/twinship-core.ttl` — Aggregate (~15 lines, imports base + all modules)
- `model/modules/*.ttl` — Domain-specific modules (vessel, weatherconditions)
- `model/external/` — Local copies of external ontologies (IDO, PAV, QUDT, VesselAI)
- `model/vocabularies/` — QUDT vocabulary files
- `model/catalog-v001.xml` — OASIS XML catalog mapping ontology URIs to local file paths
- `scripts/*.py`, `scripts/*.sh` — Build and processing scripts

### Generated artifacts (gitignored, never manually edit)

- `build/` — Intermediate `.ttl` files produced by the build pipeline
- `docs/website/` — Generated website (WIDOCO docs + WebVOWL visualization)
- `tools/` — Downloaded WIDOCO JAR
- `tmp*/` — WIDOCO temporary files

### Build artifact naming convention

Files in `build/` follow a strict naming pattern:
1. `complete.ttl` — All modules merged
2. `complete-viz.ttl` — + domain/range + virtual properties
3. `complete-docs.ttl` — TwinShip-only classes
4. `complete-docs-viz.ttl` — For WIDOCO documentation (no virtual properties)
5. `complete-viz-clean.ttl` — TwinShip + IDO only
6. `complete-viz-clean-minimal.ttl` — Final WebVOWL source (no external parents)

## Two-Pipeline Build Architecture

The website generation (`scripts/generate_website.sh`) uses separate optimized ontologies:

**Documentation Pipeline (WIDOCO):** Uses `complete-docs-viz.ttl` — original properties with multiple domains, TwinShip classes only. Shows comprehensive property tables.

**Visualization Pipeline (WebVOWL):** Uses `complete-viz-clean-minimal.ttl` — virtual properties with single domains, TwinShip + IDO classes only. Eliminates blank union nodes for clean graph.

Virtual properties (`*_viz1`, `*_viz2`) only exist in visualization build artifacts and are created by `generate_viz_ontology.py` for properties with multiple domains.

## Key Namespaces

| Prefix | URI | Notes |
|--------|-----|-------|
| `:` (default) | `https://twin-ship.eu/twinship#` | All TwinShip entities |
| base ontology | `https://twin-ship.eu/twinship/base` | Foundation |
| core ontology | `https://twin-ship.eu/twinship/core` | Aggregate |
| `ido:` | `http://rds.posccaesar.org/ontology/lis14/rdl/` | ISO 15926-14 upper ontology |
| `pav:` | `http://purl.org/pav/` | Provenance/versioning |
| `qudt:` | `http://qudt.org/schema/qudt/` | Units of measure |
| `skos:` | `http://www.w3.org/2004/02/skos/core#` | Notation, altLabel |
| `dcterms:` | `http://purl.org/dc/terms/` | Dublin Core metadata |

## Python Scripts — Conventions

- **Package manager**: `uv` (preferred). Run with `uv run python scripts/<name>.py` or activate `.venv` first.
- **Dependencies**: `rdflib>=7.0.0`, `beautifulsoup4>=4.12.0`, `lxml>=5.0.0` (see `pyproject.toml`)
- **Style**: Procedural (no classes), `pathlib.Path` for paths, `print()` with emoji for status output (not `logging`)
- **Line length**: 100 (configured for black/ruff in `pyproject.toml`)
- **Python version**: 3.9+
- **Argument parsing**: `argparse` in production scripts; some utility scripts use `sys.argv` directly
- **Error handling**: Minimal — relies on shell `set -e` and natural exceptions
- **All scripts run from repo root**

## Build Pipeline Commands

```bash
# Full website generation (the main command)
./scripts/generate_website.sh --verbose

# Individual steps (for development/debugging)
uv run python scripts/merge_modules.py --auto model/twinship-core.ttl
uv run python scripts/generate_viz_ontology.py --auto build/twinship-core-complete.ttl
uv run python scripts/generate_docs_ontology.py -o build/clean.ttl build/complete.ttl
uv run python scripts/strip_for_webvowl.py input.ttl output.ttl
uv run python scripts/generate_widoco_docs.py build/twinship-core-complete-docs-viz.ttl
uv run python scripts/enhance_widoco_html.py docs/website/documentation/index-en.html build/twinship-core-complete-docs-viz.ttl
uv run python scripts/enhance_webvowl_json.py build/twinship-core-complete-viz-clean-minimal.ttl docs/website/documentation/webvowl/data/ontology.json
```

## Prerequisites

- Python 3.9+
- Java 11+ (required for WIDOCO — `java -version` to check)
- `uv` package manager (`brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Common Pitfalls

1. **Don't add `rdfs:domain`/`rdfs:range` to source `.ttl` files** — use OWL restrictions instead
2. **Update `model/catalog-v001.xml`** when adding new ontology modules — `merge_modules.py` depends on it for URI resolution
3. **The `--auto` flag** on merge/viz scripts auto-derives output filenames — don't also specify an output path
4. **`strip_for_webvowl.py`** uses `sys.argv` (not argparse), unlike most other scripts
5. **The landing page HTML** is generated inline inside `generate_website.sh` via heredoc — edit the shell script, not the HTML file
6. **`build/` files have a specific dependency order** — later stages depend on earlier stages
7. **`tests/` directory exists but has no tests yet** — pytest is configured but unused
8. **Version mismatch**: ontology uses `pav:version` (currently "0.0.3"), `pyproject.toml` is at "0.0.1"
9. **Ontology files use UTF-8** — ensure encoding is preserved when editing `.ttl` files

## When Modifying Ontology Classes/Properties

1. Edit the appropriate source file in `model/` or `model/modules/`
2. Use OWL restriction patterns (see existing examples in `vessel.ttl`)
3. Run full build to verify: `./scripts/generate_website.sh --verbose`
4. Check both documentation and visualization output

## When Adding a New Module

1. Create `model/modules/<name>.ttl` with `owl:imports <https://twin-ship.eu/twinship/base>`
2. Add URI mapping to `model/catalog-v001.xml`
3. Add `owl:imports` to `model/twinship-core.ttl`
4. Run the build pipeline to verify integration
