"""
Pytest configuration for TwinShip ontology tests.

Loads the merged ontology once per test session so all tests share the
same in-memory graph without re-parsing on each test function.

The ontology loaded is build/twinship-core-complete.ttl — the output of
merge_modules.py. Run the build pipeline before running tests:

    uv run python scripts/merge_modules.py --auto
    uv run pytest tests/
"""

import pytest
from pathlib import Path
from rdflib import ConjunctiveGraph

ONTOLOGY_PATH = Path(__file__).parent.parent / "build" / "twinship-core-complete.ttl"


@pytest.fixture(scope="session")
def graph():
    """Parse the complete merged ontology and return the graph."""
    if not ONTOLOGY_PATH.exists():
        pytest.skip(
            f"Merged ontology not found at {ONTOLOGY_PATH}. "
            "Run 'uv run python scripts/merge_modules.py --auto' first."
        )
    g = ConjunctiveGraph()
    g.parse(str(ONTOLOGY_PATH), format="turtle")
    return g
