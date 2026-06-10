# TwinShip Ontology — Test Suite

This directory contains automated tests for the TwinShip ontology. Tests are run with [pytest](https://docs.pytest.org/) using [rdflib](https://rdflib.readthedocs.io/) to execute SPARQL queries directly against the merged ontology.

## Directory Structure

```
tests/
  conftest.py                    — pytest session fixture: loads the merged ontology once
  test_competency_questions.py   — parametrized runner: executes every .rq file in competency/
  competency/                    — one SPARQL file per competency question
    cq01_vessels_by_fleet_and_type.rq
    cq02_vessel_max_displacement.rq
    ...
    cq36_digital_twin_api_interfaces.rq
```

The human-readable catalogue of competency questions (natural language, status, notes) lives alongside the SPARQL files in [docs/ontology/competency-questions.md](../docs/ontology/competency-questions.md).

## Prerequisites

The merged ontology must exist before running tests:

```bash
uv run python scripts/merge_modules.py --auto
```

This writes `build/twinship-core-complete.ttl`, which `conftest.py` loads as the test graph.

## Running the Tests

```bash
# Run all tests with verbose output
uv run pytest tests/ -v

# Run only competency question tests
uv run pytest tests/test_competency_questions.py -v

# Show a brief summary of xfailed (not-yet-covered) CQs
uv run pytest tests/ -v --tb=no
```

## Test Modes: xfail vs STRICT

Each `.rq` file defaults to **reporting-only** (`xfail`): if the query returns no rows, the test is recorded as `xfailed` but does not block the run. This is appropriate while the ontology lacks instance data.

To promote a CQ to a **hard assertion** (required to pass), add `# STRICT` anywhere in the `.rq` file:

```sparql
# CQ-13 — Fuel LHV and sulphur content
# STRICT
SELECT ?fuel ?lhvKJPerKg ...
```

A `STRICT` test will fail (not xfail) if the query returns no results.

## Testing with Instance Data

The `conftest.py` fixture loads `build/twinship-core-complete.ttl` by default. To also load vessel instance data (gitignored under `data/`), extend the fixture or add the instance file path to `conftest.py`:

```python
INSTANCE_DATA = Path("data/vessel-instances.ttl")
if INSTANCE_DATA.exists():
    g.parse(str(INSTANCE_DATA), format="turtle")
```

Instance data files must **not** be committed to the repository — keep them under `data/` which is gitignored.

## Current Status

| Category | CQs | Status |
|----------|-----|--------|
| Vessel & Fleet Structure | CQ-01–04 | xfail (needs instance data) |
| Propulsion & Engine Configuration | CQ-05–10 | xfail (needs instance data) |
| Energy & Fuel Consumption | CQ-11–15 | CQ-13, CQ-14 pass (`:AMM`, `:BF` defined); rest xfail |
| Efficiency Enhancement Technologies | CQ-16–20 | xfail (needs instance data) |
| Emissions & Sustainability | CQ-21–24 | xfail (needs instance data) |
| Energy Storage & Alternative Power | CQ-25–26 | xfail (needs instance data) |
| Auxiliary Systems & Loads | CQ-27–29 | xfail (needs instance data) |
| Organisational & Fleet Management | CQ-30–31 | xfail (needs instance data) |
| Unmanned / Future Vessel Simulation | CQ-32–33 | xfail (needs instance data) |
| System Connectivity & Integration | CQ-34–36 | xfail (CQ-36: concept not yet modelled) |

## Adding a New Competency Question

1. Add the natural language CQ to [docs/ontology/competency-questions.md](../docs/ontology/competency-questions.md)
2. Create `tests/competency/cqNN_<slug>.rq` using the shared prefix block:

```sparql
# CQ-NN — <natural language question>
#
# Coverage: <what is needed to answer this>
# Module:   <relevant module name>

PREFIX :     <https://twin-ship.eu/twinship#>
PREFIX ido:  <http://rds.posccaesar.org/ontology/lis14/rdl/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

SELECT ...
WHERE { ... }
```

3. Run `uv run pytest tests/ -v` — the new CQ is picked up automatically
4. Update the **Test file** column in `docs/ontology/competency-questions.md`
