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

**NEVER add `rdfs:domain` to source model files** (`model/*.ttl`, `model/modules/*.ttl`).

`rdfs:domain P C` causes a reasoner to infer that every subject of property `P` is a member of class `C`. In an open-world ontology this creates incorrect inferences — for example, `rdfs:domain :hasQuality :VesselSystem` would misclassify any `VoyageLeg` or `Port` that uses `:hasQuality` as a `:VesselSystem`. Use OWL class restrictions (`owl:someValuesFrom`, `owl:allValuesFrom`) on classes to express which classes are expected to use a property.

There is also a **build pipeline dependency**: `generate_viz_ontology.py` synthesizes `rdfs:domain` by reading OWL restrictions. If source files already contained `rdfs:domain`, the script would produce duplicate or incorrectly paired domain-range assertions in the visualization output.

`rdfs:domain` assertions exist **only** in auto-generated files (`build/*-viz*.ttl`), where they are synthesized from OWL restrictions by `generate_viz_ontology.py` for WIDOCO/WebVOWL tooling compatibility.

**`rdfs:range` IS used in source files and is required:**
- **Datatype properties**: always declare `rdfs:range` with an XSD type (`xsd:decimal`, `xsd:dateTime`, `xsd:string`, etc.) — this is standard OWL/RDFS with no alternative.
- **Object properties**: `rdfs:range` constrains what the property value must be. Unlike `rdfs:domain`, this infers the *value's* type (not the subject's), which is the intended constraint.
- **Build pipeline dependency**: `generate_viz_ontology.py` reads `rdfs:range` from source property definitions and combines it with restriction-derived `rdfs:domain` to produce the paired assertions in viz output. `rdfs:range` must be present in source files.

**In summary:** the restriction-based principle applies to *domain* constraints only. OWL restrictions define which classes use a property; `rdfs:range` on properties defines what the value must be. The build scripts rely on this exact split.

**Applying restrictions — required for every class in every module:**

Every class must declare `rdfs:subClassOf` restrictions for all object and data properties that are characteristic of it. This applies to **all modules**, not just `vessel.ttl`. Use `owl:someValuesFrom` for both object and datatype properties:

```turtle
:MyClass rdfs:subClassOf
    [ a owl:Restriction ; owl:onProperty :hasRelatedThing   ; owl:someValuesFrom :RelatedClass ],
    [ a owl:Restriction ; owl:onProperty :twMyDataProperty  ; owl:someValuesFrom xsd:decimal ] .
```

This is what Protégé shows as "subclass of `twinship my data property`" and "subclass of `hasRelatedThing some RelatedClass`" — they are anonymous restriction classes, not direct class-to-class or class-to-property relationships. The `generate_viz_ontology.py` build script reads these restrictions to synthesize `rdfs:domain` in the visualization output, so missing restrictions means the property will not appear in the WebVOWL graph.

## Naming Conventions

All TwinShip entity names are in the shared `twinship#` namespace (`:` prefix). These conventions apply to **all modules** — follow them when adding new terms.

| Category | Pattern | Examples |
|---|---|---|
| Foundation classes | `TwinShip` + PascalCase | `:TwinShipQuality`, `:TwinShipProcess`, `:TwinShipInanimatePhysicalObject` |
| Domain classes | Plain PascalCase | `:VesselSystem`, `:OperatingState`, `:Voyage` |
| Acronym classes | ALL-CAPS | `:CPP`, `:FPP`, `:PTO` |
| Object properties | lowerCamelCase (`has<Thing>` dominant) | `:hasOperatingState`, `:followsRoute`, `:hasFuelConsumptionSummary` |
| **Data properties** | **`tw` + UpperCamelCase + optional unit suffix** | **`:twBoilerPowerMaxInKW`, `:twVoyageDurationHours`, `:twWindSpeed`** |
| **Data property labels** | **`"twinship <descriptive name>"` (lowercase)** | **`"twinship voyage duration hours"`, `"twinship wind speed"`** |
| Named individuals (descriptive) | PascalCase | `:CruiseState`, `:EvenKeel`, `:SternTrim` |
| Named individuals (abbreviations) | ALL-CAPS | `:HFO`, `:MGO`, `:CPP` |
| Ontology IRIs | kebab-case path | `https://twin-ship.eu/twinship/operational-modes` |

**Unit suffix convention for data properties** (established in `vessel.ttl`):
- `InM` — metres; `InKW` — kilowatts; `InMT` — metric tonnes; `InDegC` — degrees Celsius
- `InRevPerMin` — RPM; `KgPerHr` — kg/hr; `KJPerKg` — kJ/kg
- No unit suffix for dimensionless ratios, counts, string identifiers, or `xsd:dateTime` properties

**Do NOT** use plain lowerCamelCase for data properties (e.g., `:windSpeed`, `:voyageIdentifier`) — always use the `tw` prefix.

## Repository Structure

### Source files (version-controlled, manually edited)

- `model/twinship-base.ttl` — Foundation layer (base classes, properties)
- `model/twinship-core.ttl` — Aggregate (~15 lines, imports base + all modules)
- `model/modules/*.ttl` — Domain-specific modules (vessel, weather-conditions, operational-modes, operational-context)
  - **`model/modules/weather-conditions.ttl`** — Canonical module for TwinShip-native weather and wind conditions: `WeatherCondition` (subClassOf `TwinShipQuality`), `WindCondition` (subClassOf `WeatherCondition`), `hasWeatherCondition`, `hasWindCondition`, `windSpeed`, `windDirection`. Does **not** import VesselAI, DUL, GeoSPARQL, or OWL-Time. IRI: `https://twin-ship.eu/twinship/weather-conditions`.
  - **`model/modules/operational-modes.ttl`** — Canonical module for all categorical operational states and modes: `OperatingState`, `EngineMode`, `DraftMode`, `TrimMode`, `DraftTrimMode`, and related individuals (CruiseState, EvenKeel, SternTrim, etc.). Use this file for all new mode/state concepts. IRI: `https://twin-ship.eu/twinship/operational-modes`.
  - **`model/modules/operational-context.ttl`** — Canonical module for operational context: `Voyage`, `VoyageLeg`, `Route`, `Port`, `OperationalProfile`, `SpeedBin`, `FrequencyDistribution`, `FuelConsumptionObservation`, `FuelConsumptionSummary`, and related voyage/context/statistical-summary properties and data properties. IRI: `https://twin-ship.eu/twinship/operational-context`. Imports: `twinship-base` + `operational-modes` (references `:OperatingState` in property range constraints).
  - **Do NOT** add new mode/state classes to `operational-context.ttl`. Mode and state concepts belong in `operational-modes.ttl`.
  - **Do NOT** add voyage or context concepts to `operational-modes.ttl`.
  - **Do NOT** import VesselAI into any TwinShip module. **VesselAI is not currently imported by TwinShip.** The `owl:imports <http://www.vesselAI-project.eu/vesselai>` statement has been removed from `twinship-base.ttl`. VesselAI uses DUL/DOLCE as its upper ontology, which is incompatible with IDO; importing it would pull DUL, GeoSPARQL, and OWL-Time into the import closure. The files under `model/external/vesselai/` are retained for inspection and reference only. The full design decision is documented in `docs/ontology/vesselai-full-reuse-audit.txt`.
  - **Do NOT** reference VesselAI terms using `owl:equivalentClass` or `skos:closeMatch`. VesselAI's `WeatherCondition` is a `dul:Event`; TwinShip's `WeatherCondition` is a `TwinShipQuality` — these are genuinely different semantic categories. Use `rdfs:seeAlso` only for source traceability. `skos:relatedMatch` is acceptable for `:VesselSystem` / `VAI:Vessel` and `:FuelConsumptionSummary` / `VAI:CO2_emissionReport` where the domain concepts are closely related, but never `skos:closeMatch` or OWL equivalence.
  - A future `operational-requirements.ttl` module is reserved for requirements/constraints (ETARequirement, SpeedRequirement, RouteRequirement, FuelRequirement, EmissionRequirement, WeatherConstraint, PortConstraint). Do not add `Voyage`, `VoyageLeg`, `Route`, or `Port` to that module when it is created.
  - Do not create or reference `draft-trim-mode.ttl`, `draft_time_mode.ttl`, `draft_trim_mode.ttl`, `operations.ttl`, or `weatherconditions.ttl` — those were replaced by the canonical modules listed above.
- `model/external/` — Local copies of external ontologies (IDO, PAV, QUDT). The `vesselai/` subdirectory contains VesselAI ontology files retained for inspection and reference **only** — they are **not imported** by any TwinShip module. See `docs/ontology/vesselai-full-reuse-audit.txt`.
- `model/vocabularies/` — QUDT vocabulary files
- `model/catalog-v001.xml` — OASIS XML catalog mapping ontology URIs to local file paths
- `scripts/*.py`, `scripts/*.sh` — Build and processing scripts
- `docs/ontology/` — Ontology design decision reports (e.g., `vesselai-full-reuse-audit.txt`)
- `queries/` — SPARQL validation queries

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

1. **Don't add `rdfs:domain` to source `.ttl` files** — use OWL restrictions instead. (`rdfs:range` IS required in source files — see "Restriction-Based Modeling" above)
2. **Update `model/catalog-v001.xml`** when adding new ontology modules — `merge_modules.py` depends on it for URI resolution
3. **The `--auto` flag** on merge/viz scripts auto-derives output filenames — don't also specify an output path
4. **`strip_for_webvowl.py`** uses `sys.argv` (not argparse), unlike most other scripts
5. **The landing page HTML** is generated inline inside `generate_website.sh` via heredoc — edit the shell script, not the HTML file
6. **`build/` files have a specific dependency order** — later stages depend on earlier stages
7. **`tests/` directory exists but has no tests yet** — pytest is configured but unused
8. **Version synchronization**: All version numbers are synchronized to "0.0.4" across ontology files and project metadata
9. **Ontology files use UTF-8** — ensure encoding is preserved when editing `.ttl` files

## When Modifying Ontology Classes/Properties

1. Edit the appropriate source file in `model/` or `model/modules/`
2. Use OWL restriction patterns (see existing examples in `vessel.ttl`)
3. Run full build to verify: `./scripts/generate_website.sh --verbose`
4. Check both documentation and visualization output

## When Adding a New Module

1. Create `model/modules/<name>.ttl` with `owl:imports <https://twin-ship.eu/twinship/base>`. If the new module references classes defined in another module (e.g., `:OperatingState` from `operational-modes`), also import that module — cross-module imports are permitted provided they form a strict DAG (no circular dependencies).
2. Add URI mapping to `model/catalog-v001.xml`
3. Add `owl:imports` to `model/twinship-core.ttl`
4. Run the build pipeline to verify integration
