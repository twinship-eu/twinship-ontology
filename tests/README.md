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

## Synthetic Test Repository (Public, No Confidential Data)

The file `tests/data/twinship-test-instances.ttl` contains fully synthetic
vessel instance data.  It uses three fictional vessels:

| Individual | Type | Key systems |
|---|---|---|
| `td:Vessel1` | RoPax | Mechanical drive, FourStroke, FPP, GearboxSystem, ShaftGenerator, SCR, BowThruster, ALS, AuxEngine, AUXLOAD, OSP |
| `td:Vessel2` | RoRo | Mechanical drive, TwoStroke, FPP, WASP, DynamicWing, GateRudder, AuxEngine, AUXLOAD |
| `td:Vessel3` | RoRo (futuristic) | Diesel-electric, GenSet×2, CPP, FreqConverter, ESS, BidirConverter, AUXLOAD (unmanned) |

No real vessel names, IMO numbers, or operator identities are used.  The file
can be committed to the public repository and loaded into any GraphDB instance.

### Loading test data into GraphDB

```bash
# Uses GRAPHDB_URL (default http://localhost:7200) and
# GRAPHDB_TEST_REPO (default vessel-test).
uv run python scripts/load_test_instances.py
```

The script creates the `vessel-test` repository if it does not exist, clears
any previous data, and loads the TTL into the default graph.

### Running CQ tests in strict mode against the test repo

```bash
uv run pytest tests/ \
  --graphdb-url http://localhost:7200 \
  --graphdb-test-repo vessel-test \
  -v
```

In test-repo mode **all 35 CQs** (CQ-01..CQ-35) are treated as **strict
assertions** — they must return at least one result row or the test fails.
CQ-36 is exempt because the API-interface concept is not yet modelled.

This mode is suitable for CI: it validates that the full ontology (schema +
instance data) correctly answers every defined competency question.

## Testing with Live GraphDB Instance Data

The `twinship-data-pipeline` repository provides a `docker-compose.yml` stack that runs GraphDB at `localhost:7200` with four test vessels loaded as separate repositories.

| Default placeholder | Vessel type |
|---|---|
| `vessel-roro` | RoRo |
| `vessel-ropax` | RoPax |
| `vessel-tanker` | Tanker |
| `vessel-futuristic` | RoRo futuristic |

The default repository IDs above are generic placeholders. The actual IDs in GraphDB are set by the data-pipeline; pass them via `--graphdb-repos` when running tests.

### Starting the stack

```bash
cd ../twinship-data-pipeline
docker-compose up -d
# Run the Dagster pipeline to load vessel data into GraphDB
```

### Running CQ tests against GraphDB

Pass `--graphdb-url` to switch from rdflib to live SPARQL queries. Results are
automatically combined across all configured vessel repositories.

You must also pass `--graphdb-repos` with the actual repository IDs from your
GraphDB instance (the data-pipeline sets these when loading vessel data).

GraphDB uses Keycloak OpenID authentication. Credentials are **not stored in
this repository** — obtain them from the `twinship-data-pipeline` deployment
configuration and set them as environment variables before running tests.

Provide credentials via one of:

**Option A — Keycloak client credentials (token fetched automatically):**
```bash
KEYCLOAK_CLIENT_ID=<your-client-id> \
KEYCLOAK_CLIENT_SECRET=<your-client-secret> \
uv run pytest tests/ \
  --graphdb-url http://localhost:7200 \
  --graphdb-repos <repo1>,<repo2>,<repo3>,<repo4> \
  -v
```

**Option B — Pre-acquired bearer token:**
```bash
# Get a token manually from Keycloak
TOKEN=$(curl -s -X POST http://localhost:8080/realms/twinship/protocol/openid-connect/token \
  -d "grant_type=client_credentials&client_id=<your-client-id>&client_secret=<your-client-secret>" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

GRAPHDB_TOKEN=$TOKEN uv run pytest tests/ \
  --graphdb-url http://localhost:7200 \
  --graphdb-repos <repo1>,<repo2>,<repo3>,<repo4> \
  -v
```

### Specifying the repository list

`--graphdb-repos` is required when using `--graphdb-url`; the default placeholders will not match real GraphDB repo IDs:

```bash
# Specify the actual repository IDs from your GraphDB instance
uv run pytest tests/ --graphdb-url http://localhost:7200 \
  --graphdb-repos <repo1>,<repo2>
```

### How it works

`conftest.py` detects `--graphdb-url` and returns a `GraphDBFederatedSparql` client instead of an rdflib graph. The client:

1. Posts each `.rq` query to every configured GraphDB repository's SPARQL endpoint
2. Combines and deduplicates results across repositories
3. Returns a list that `test_competency_questions.py` can use unchanged

No changes to the `.rq` query files are required.

## Current Status

| Category | CQs | Schema-only (rdflib) | Test-repo mode |
|----------|-----|----------------------|----------------|
| Vessel & Fleet Structure | CQ-01–04 | xfail | strict ✓ |
| Propulsion & Engine Configuration | CQ-05–10 | xfail | strict ✓ |
| Energy & Fuel Consumption | CQ-11–15 | CQ-13,14 pass; rest xfail | strict ✓ |
| Efficiency Enhancement Technologies | CQ-16–20 | xfail | strict ✓ |
| Emissions & Sustainability | CQ-21–24 | xfail | strict ✓ |
| Energy Storage & Alternative Power | CQ-25–26 | xfail | strict ✓ |
| Auxiliary Systems & Loads | CQ-27–29 | xfail | strict ✓ |
| Organisational & Fleet Management | CQ-30–31 | xfail | strict ✓ |
| Unmanned / Future Vessel Simulation | CQ-32–33 | xfail | strict ✓ |
| System Connectivity & Integration | CQ-34–35 | xfail | strict ✓ |
| Digital Twin API (future) | CQ-36 | xfail | xfail (not yet modelled) |

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
