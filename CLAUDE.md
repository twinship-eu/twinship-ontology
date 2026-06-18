# CLAUDE.md — TwinShip Ontology Agent Context

## Purpose

TwinShip is an OWL ontology for maritime vessel digital twins. Primary artifacts are Turtle (`.ttl`) ontology files. Python scripts are build/documentation tooling only.

Be concise. Prefer minimal diffs, short answers, and focused context.

---

## Token-Saving Rules

1. Prefer inline/code edits over long explanations.
2. For small tasks, skip formal planning and act directly.
3. For non-trivial tasks, provide a short plan only:
   - Goal
   - Files likely changed
   - Steps
   - Risks/checks
4. Do not restate repository rules unless relevant.
5. Do not paste large file excerpts unless asked.
6. Ask for only the missing information needed to proceed.
7. Use the cheapest/smallest suitable model for routine edits.
8. Limit outputs:
   - summaries: max 5 bullets
   - plans: max 6 steps
   - explanations: short unless asked for detail
9. For generated code or TTL, output only the changed block or patch when possible.
10. Do not run broad repo-wide analysis unless requested.

---

## Workflow Rules

For non-trivial changes:

1. Analyze request.
2. Give a short implementation plan.
3. Wait for user approval.
4. Implement approved changes.
5. Report changed files and result.

Skip planning for:
- reading files
- searching
- quick status checks
- small edits
- simple explanations

Never include git operations in plans. Do not suggest staging, committing, or pushing unless explicitly asked.

After implementation:
- summarize what changed
- list modified files
- stop

---

## Critical Ontology Rule: No `rdfs:domain` in Source

Never add `rdfs:domain` to source ontology files:

- `model/*.ttl`
- `model/modules/*.ttl`

Use OWL restrictions on classes instead.

Reason:
- `rdfs:domain` causes broad subject-type inference.
- TwinShip uses restriction-based modeling.
- `generate_viz_ontology.py` derives visualization domains from restrictions.
- Source `rdfs:domain` would cause incorrect or duplicate visualization output.

`rdfs:domain` is allowed only in generated files under `build/`.

`rdfs:range` is required in source files:
- datatype properties: use XSD ranges
- object properties: use class ranges

---

## Required Class Restriction Pattern

Every class must declare `rdfs:subClassOf` restrictions for characteristic object and data properties.

Use `owl:someValuesFrom` for both object and datatype properties.

Example:

```turtle
:MyClass rdfs:subClassOf
    [ a owl:Restriction ;
      owl:onProperty :hasRelatedThing ;
      owl:someValuesFrom :RelatedClass ],
    [ a owl:Restriction ;
      owl:onProperty :twMyDataProperty ;
      owl:someValuesFrom xsd:decimal ] .
```

Restrictions are required because the visualization pipeline derives property domains from them.

---

## QUDT Quantity and Unit Pattern

TwinShip uses QUDT as the preferred approach for quantities and units, following the **Nexus advanced pattern** (see `model/external/nexus/model/nexus-core-advanced.ttl`).

The QUDT vocabulary file is `model/twinship-qudt-vocabulary.ttl`, imported by `twinship-base.ttl` (and therefore available to all domain modules automatically). It adds **22 quantity kind families**, each comprising:

```turtle
# Per quantity kind X:
:TwinShipQuantityKindFor[X] rdfs:subClassOf qudt:QuantityKind .
:TwinShipUnitFor[X]         rdfs:subClassOf qudt:Unit .
:TwinShipQuantityValue[X]   rdfs:subClassOf qudt:QuantityValue .
:TwinShipQuantity[X]        rdfs:subClassOf qudt:Quantity ,
    [ owl:onProperty qudt:hasQuantityKind ; owl:allValuesFrom :TwinShipQuantityKindFor[X] ] ,
    [ owl:onProperty qudt:quantityValue   ; owl:allValuesFrom :TwinShipQuantityValue[X]   ] .

:hasQuantity[X] rdfs:subPropertyOf qudt:hasQuantity ;
    rdfs:range :TwinShipQuantity[X] .

# Type the QUDT named individuals as family members:
quantitykind:[X] a :TwinShipQuantityKindFor[X] .
unit:[Y]         a :TwinShipUnitFor[X] .

# Domain class restriction:
:MyClass rdfs:subClassOf
    [ owl:onProperty :hasQuantity[X] ; owl:someValuesFrom :TwinShipQuantity[X] ] .
```

**Coexistence with XSD data properties** (explicit policy):

The existing `tw`-prefixed `owl:DatatypeProperty` declarations with `rdfs:range xsd:double` / `xsd:decimal` are **retained unchanged**. They serve as the pragmatic SPARQL query layer. The QUDT object properties provide semantic grounding and unit disambiguation. Both layers must be maintained.

Rule: when adding a new numeric data property:
1. Add the `hasQuantity[X]` family definition (4 classes + 1 property + QUDT individual type assertions) to `twinship-qudt-vocabulary.ttl`.
2. Add the `owl:someValuesFrom` restriction to the owning class in the relevant domain module (`vessel.ttl`, `operational-context.ttl`, or `weather-conditions.ttl`).

---

## Naming Rules

All TwinShip terms use the `:` prefix:

```turtle
: <https://twin-ship.eu/twinship#>
```

Use these patterns:

- Foundation classes: `TwinShip` + PascalCase  
  Example: `:TwinShipQuality`

- Domain classes: PascalCase  
  Example: `:VesselSystem`

- Acronym classes/individuals: ALL-CAPS  
  Example: `:CPP`, `:HFO`

- Object properties: lowerCamelCase  
  Example: `:hasOperatingState`

- Data properties: `tw` + UpperCamelCase + optional unit suffix  
  Example: `:twWindSpeedInKnots`

- Data property labels: sentence case  
  Example: `"Wind speed in knots"`

Do not use plain lowerCamelCase for data properties.

Common unit suffixes:
- `InM`
- `InKW`
- `InMT`
- `InDegC`
- `InRevPerMin`
- `KgPerHr`
- `KJPerKg`

No unit suffix for dimensionless values, counts, identifiers, or date/time values.

---

## Standards Traceability

If a data property matches an IMO or ISO definition, add these together:

```turtle
skos:notation
skos:altLabel
dcterms:description
dcterms:source
```

See `model/README.md` for examples.

Use:

```bash
uv run python scripts/align_imo.py --prepare   # writes data/imo_alignment_review.csv
uv run python scripts/align_imo.py --apply --dry-run
uv run python scripts/align_imo.py --apply
```

In `data/imo_alignment_review.csv`, set the `action` column on the best candidate row:
- `confirm` — inject this IMO code into the `.ttl` file
- `reject` — no IMO equivalent; leave unannotated
- `iso` — aligned to ISO or another standard; leave unannotated

Prerequisite (first run only):

```bash
uv run python scripts/extract_imo_compendium.py
```

---

## Repository Structure

Committed source:
- `model/`
- `model/modules/`
- `model/external/`

Generated or transient:
- `build/` — generated, do not edit
- `docs/website/documentation/` — generated, do not edit
- `data/` — gitignored working data/cache
- `papers/` — gitignored; SWJ paper planning/readiness files (local only, never committed)

Scripts:

```bash
uv run python scripts/<script>.py
```

Full build:

```bash
./scripts/generate_website.sh --verbose
```

Key namespaces:
- `:` → `https://twin-ship.eu/twinship#` — all TwinShip entities
- `ido:` → `http://rds.posccaesar.org/ontology/lis14/rdl/` — upper ontology (ISO 15926-14)

See:
- `model/README.md` for ontology structure
- `scripts/README.md` for build details

---

## Module Boundaries

Keep concepts in the correct module.

- `operational-modes.ttl`  
  States/modes and named individuals:
  `OperatingState`, `EngineMode`, `DraftMode`, `TrimMode`, `DraftTrimMode`

- `operational-context.ttl`  
  Voyage, leg, port, route, profiles, observations, summaries

- `weather-conditions.ttl`  
  Weather/wind conditions and wind data properties

- `vessel.ttl`  
  Vessel systems, engines, propulsion, fuel, gearbox. Includes QUDT `owl:someValuesFrom` restrictions for all vessel-domain classes.

- `qudt-quantities.ttl`  
  **Removed.** QUDT family class/property definitions are now in `twinship-qudt-vocabulary.ttl` (imported by base). Domain class restrictions are in the respective domain module files.

Reserved future module:
- `operational-requirements.ttl`

Do not create or reference obsolete modules:
- `draft-trim-mode.ttl`
- `draft_time_mode.ttl`
- `operations.ttl`
- `weatherconditions.ttl`
- `qudt-quantities.ttl` (superseded by `twinship-qudt-vocabulary.ttl` + per-module restrictions)

---

## VesselAI Rules

Do not import VesselAI into TwinShip modules.

Do not use:
- `owl:equivalentClass` with VesselAI terms
- `skos:closeMatch` with VesselAI terms

VesselAI is retained only as external reference material under:

```text
model/external/vesselai/
```

Use:
- `rdfs:seeAlso` for traceability
- `skos:relatedMatch` only for closely related concepts

Reason: VesselAI depends on DUL/DOLCE and is incompatible with the IDO-based TwinShip modeling approach.

---

## Build Pipeline

Full website/documentation build:

```bash
./scripts/generate_website.sh --verbose
```

Main outputs:
- WIDOCO documentation uses `complete-docs-viz.ttl`
- WebVOWL visualization uses `complete-viz-clean-minimal.ttl`

Never manually edit generated files in:
- `build/`
- `docs/website/documentation/`

---

## Common Pitfalls

1. Do not add `rdfs:domain` to source `.ttl` files.
2. Always add `rdfs:range` to source properties.
3. Add class restrictions for characteristic properties.
4. Update `model/catalog-v001.xml` when adding modules.
5. Add new module imports to `model/twinship-core.ttl`.
6. Do not combine `--auto` with explicit output paths.
7. `strip_for_webvowl.py` uses `sys.argv`, not `argparse`.
8. Edit landing page HTML inside `generate_website.sh`.
9. **UTF-8 encoding — three layers; do not remove any:**
   - `.env` at repo root sets `PYTHONUTF8=1` — `uv run` loads it automatically.
   - All Python file I/O uses explicit `encoding='utf-8'` — never use bare `open(path)`.
   - WIDOCO Java is invoked with `-Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8`.
10. **Version synchronization** — all version numbers must stay in sync (currently `0.0.4`) across ontology files and project metadata.

---

## Testing Competency Questions

CQ tests run in two modes — select based on what you need:

**Schema-only (default):** validates ontology structure against the merged TTL.
```bash
uv run python scripts/merge_modules.py --auto
uv run pytest tests/ -v
```
Most CQs will `xfail` (no instance data). Add `# STRICT` to a `.rq` file to make it a hard failure.

**Live GraphDB (instance data):** queries all vessel repositories in a running GraphDB instance.
```bash
KEYCLOAK_CLIENT_ID=<your-client-id> \
KEYCLOAK_CLIENT_SECRET=<your-client-secret> \
uv run pytest tests/ \
  --graphdb-url http://localhost:7200 \
  --graphdb-repos <repo1>,<repo2>,<repo3>,<repo4> \
  -v
```

GraphDB is provided by the `twinship-data-pipeline` stack (`docker-compose up`). Credentials and repository IDs come from that deployment — **do not commit them**. See `tests/README.md` for full options.

Privacy rules for tests:
- No operator names, vessel names, or instance identifiers in committed test files.
- `--graphdb-repos` defaults to generic placeholders (`vessel-roro`, etc.) — always override at runtime.
- Credentials are passed only via environment variables, never stored in files.

---

## Adding a New Module

1. Create `model/modules/<name>.ttl` with `owl:imports <https://twin-ship.eu/twinship/base>`.
   - Cross-module imports are allowed if they form a strict DAG (no cycles).
   - If the module uses classes from another module (e.g. `:OperatingState`), also import that module.
2. Add URI mapping to `model/catalog-v001.xml`.
3. Add `owl:imports` to `model/twinship-core.ttl`.
4. Run the build pipeline to verify integration:

```bash
./scripts/generate_website.sh --verbose
```

---

## Adding or Modifying Ontology Terms

1. Edit the relevant source `.ttl` file.
2. Follow naming rules.
3. Add `rdfs:range` to properties.
4. Add OWL restrictions to classes.
5. Run:

```bash
./scripts/generate_website.sh --verbose
```

6. Check documentation and visualization outputs.