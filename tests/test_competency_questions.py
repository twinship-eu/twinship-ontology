"""
Competency question tests for the TwinShip ontology.

Each .rq file in tests/competency/ is a SPARQL SELECT query that encodes
one competency question (CQ). A CQ is considered answered if the query
returns at least one result row against the merged ontology.

Test mode: REPORTING ONLY — failures are collected and reported but do not
block the test run (xfail with run=True). Promote individual CQs to strict
assertions (remove xfail) once the ontology fully covers them.

To run:
    uv run pytest tests/test_competency_questions.py -v
    uv run pytest tests/test_competency_questions.py -v --tb=short
"""

import pytest
from pathlib import Path
from rdflib import ConjunctiveGraph

CQ_DIR = Path(__file__).parent / "competency"

# Collect all .rq files; skip gracefully if the directory is empty.
cq_files = sorted(CQ_DIR.glob("*.rq")) if CQ_DIR.exists() else []


@pytest.mark.parametrize("rq_file", cq_files, ids=[f.stem for f in cq_files])
def test_competency_question(rq_file: Path, graph: ConjunctiveGraph):
    """
    Execute a competency question query and assert at least one result row.

    The test is marked xfail (reporting-only) by default. To make a CQ a
    hard requirement, add a # STRICT comment anywhere in the .rq file.
    """
    query_text = rq_file.read_text(encoding="utf-8")
    is_strict = "# STRICT" in query_text

    results = list(graph.query(query_text))

    if is_strict:
        assert len(results) > 0, (
            f"Competency question '{rq_file.stem}' returned no results — "
            "ontology does not yet cover this CQ."
        )
    else:
        if len(results) == 0:
            pytest.xfail(
                f"Competency question '{rq_file.stem}' returned no results — "
                "ontology does not yet fully cover this CQ (reporting-only)."
            )
