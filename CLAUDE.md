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
| **Data properties** | **`tw` + UpperCamelCase + optional unit suffix** | **`:twBoilerPowerMaxInKW`, `:twVoyageDurationHours`, `:twWindSpeedInKnots`** |
| **Data property labels** | **Sentence-case descriptive name (first letter capitalised)** | **`"Voyage duration hours"`, `"Wind speed in knots"`** |
| Named individuals (descriptive) | PascalCase | `:CruiseState`, `:EvenKeel`, `:SternTrim` |
| Named individuals (abbreviations) | ALL-CAPS | `:HFO`, `:MGO`, `:CPP` |
| Ontology IRIs | kebab-case path | `https://twin-ship.eu/twinship/operational-modes` |

**Unit suffix convention for data properties** (established in `vessel.ttl`):
- `InM` — metres; `InKW` — kilowatts; `InMT` — metric tonnes; `InDegC` — degrees Celsius
- `InRevPerMin` — RPM; `KgPerHr` — kg/hr; `KJPerKg` — kJ/kg
- No unit suffix for dimensionless ratios, counts, string identifiers, or `xsd:dateTime` properties

**Do NOT** use plain lowerCamelCase for data properties (e.g., `:windSpeed`, `:voyageIdentifier`) — always use the `tw` prefix.

**Standards-based naming and traceability for data properties:**

When a data property corresponds to an IMO (preferred) or ISO standard definition, annotate it with all four triples together: `skos:notation`, `skos:altLabel`, `dcterms:description`, `dcterms:source`. See `model/README.md` → "Standards Traceability for Data Properties" for full examples and the IMO Compendium CSV (`model/external/imo/imo_compendium_all.csv`).

## Repository Structure

Source files are in `model/` (committed) and scripts in `scripts/`. See `model/README.md` for the full directory tree and module descriptions. See `scripts/README.md` for the build pipeline and Python coding conventions. Run scripts with `uv run python scripts/<name>.py` from the repo root.

**Directory split — committed vs gitignored:**
- `model/` — ontology source files and external reference data; everything here is committed
- `data/` — gitignored entirely; use for transient working artifacts, vessel instance data, and download caches (e.g., `data/IMO_Compendium.xlsx`, `data/imo_candidates.csv`)
- `build/` and `docs/website/documentation/` — generated by the build pipeline; **never manually edit these**

**Key namespaces:**
- `:` → `https://twin-ship.eu/twinship#` — all TwinShip entities
- `ido:` → `http://rds.posccaesar.org/ontology/lis14/rdl/` — upper ontology (ISO 15926-14)

### Module Boundaries

Each module has a clearly defined responsibility. Do not mix concepts across modules:

- **`operational-modes.ttl`** — all categorical states/modes (`OperatingState`, `EngineMode`, `DraftMode`, `TrimMode`, `DraftTrimMode`) and their named individuals. **Do NOT add mode/state classes to `operational-context.ttl`.**
- **`operational-context.ttl`** — voyage, leg, port, route, profiles, observations, summaries. **Do NOT add voyage/context concepts to `operational-modes.ttl`.**
- **`weather-conditions.ttl`** — `WeatherCondition`, `WindCondition`, wind data properties. Does not import VesselAI, DUL, GeoSPARQL, or OWL-Time.
- **`vessel.ttl`** — vessel systems, engines, propulsion, fuel, gearbox.
- A future **`operational-requirements.ttl`** is reserved for requirements/constraints (ETARequirement, SpeedRequirement, etc.). Do not pre-populate `Voyage`/`Port`/`Route` there.
- **Do not create or reference** `draft-trim-mode.ttl`, `draft_time_mode.ttl`, `operations.ttl`, or `weatherconditions.ttl` — those were replaced by the canonical modules above.

### VesselAI

**Do NOT import VesselAI** into any TwinShip module. `owl:imports <http://www.vesselAI-project.eu/vesselai>` has been removed from `twinship-base.ttl`. VesselAI uses DUL/DOLCE (incompatible with IDO) — importing it would pull DUL, GeoSPARQL, and OWL-Time into the closure. Files under `model/external/vesselai/` are retained for reference only. See `docs/ontology/vesselai-full-reuse-audit.txt`.

**Do NOT** use `owl:equivalentClass` or `skos:closeMatch` with VesselAI terms. VesselAI's `WeatherCondition` is a `dul:Event`; TwinShip's is a `TwinShipQuality` — genuinely different. Use `rdfs:seeAlso` for traceability; `skos:relatedMatch` is acceptable for closely related domain concepts (`:VesselSystem`/`VAI:Vessel`).

## Build Pipeline

```bash
./scripts/generate_website.sh --verbose   # full website generation
```

Two pipelines: **Documentation** (WIDOCO, uses `complete-docs-viz.ttl`) and **Visualization** (WebVOWL, uses `complete-viz-clean-minimal.ttl`). See `scripts/README.md` for individual step commands and Python coding conventions.

## Common Pitfalls

1. **Don't add `rdfs:domain` to source `.ttl` files** — use OWL restrictions instead. (`rdfs:range` IS required in source files — see "Restriction-Based Modeling" above)
2. **Update `model/catalog-v001.xml`** when adding new ontology modules — `merge_modules.py` depends on it for URI resolution
3. **The `--auto` flag** on merge/viz scripts auto-derives output filenames — don't also specify an output path
4. **`strip_for_webvowl.py`** uses `sys.argv` (not argparse), unlike most other scripts
5. **The landing page HTML** is generated inline inside `generate_website.sh` via heredoc — edit the shell script, not the HTML file
6. **`build/` and `docs/website/documentation/` are generated by the pipeline — never manually edit them.** Edit source `.ttl` files in `model/` and re-run `./scripts/generate_website.sh`. The `build/` stages also have a strict dependency order — later stages depend on earlier ones.
7. **`tests/` directory exists but has no tests yet** — pytest is configured but unused
8. **Version synchronization**: All version numbers are synchronized to "0.0.4" across ontology files and project metadata
9. **Ontology files use UTF-8** — ensure encoding is preserved when editing `.ttl` files
10. **Windows UTF-8 encoding** — three layers of protection are in place; do not remove them:
    - **`.env`** at repo root sets `PYTHONUTF8=1` — `uv run` loads this automatically, fixing emoji `print()` output on Windows consoles. `.vscode/settings.json` sets `python.terminal.useEnvFile: true` so VS Code terminals pick it up too.
    - **All file I/O** in Python scripts uses explicit `encoding='utf-8'` — never use bare `open(path)` or `Path.write_text(content)` without `encoding='utf-8'`.
    - **WIDOCO Java** invocation passes `-Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8` so `ontology.json` is written in UTF-8. A cp1252 fallback reader remains in `enhance_webvowl_json.py` for any previously generated files.

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
