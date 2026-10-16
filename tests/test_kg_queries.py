"""
Knowledge-graph retrieval queries for the TwinShip ontology.

Each .rq file in tests/kg/ is a SPARQL SELECT query that retrieves data from
a populated KG (voyages, legs, weather, ...). These are not competency
questions: a query passes when it returns at least one row.

They need instance data, so they run only with --graphdb-url and are skipped
in schema-only mode and in --graphdb-test-repo mode (the synthetic test
repository has no voyage data).

To run:
    uv run pytest tests/test_kg_queries.py -v \\
        --graphdb-url http://localhost:7200 --graphdb-repos <repo-id>
"""

from pathlib import Path
from typing import Any

import pytest

KG_DIR = Path(__file__).parent / "kg"
kg_files = sorted(KG_DIR.glob("*.rq")) if KG_DIR.exists() else []


def _description(query_text: str) -> str:
    for line in query_text.splitlines():
        if line.startswith("# KG-"):
            return line[2:].strip()
    return ""


@pytest.mark.parametrize("rq_file", kg_files, ids=[f.stem for f in kg_files])
def test_kg_query(rq_file: Path, graph: Any, request: pytest.FixtureRequest) -> None:
    if not request.config.getoption("--graphdb-url"):
        pytest.skip("KG queries need instance data: pass --graphdb-url")
    if request.config.getoption("--graphdb-test-repo"):
        pytest.skip("KG queries need voyage data, not in the synthetic test repository")

    query_text = rq_file.read_text(encoding="utf-8")
    rows = list(graph.query(query_text))
    assert rows, f"{rq_file.stem} returned no rows: {_description(query_text)}"
