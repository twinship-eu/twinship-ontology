"""
Competency question tests for the TwinShip ontology.

Each .rq file in tests/competency/ is a SPARQL SELECT query that encodes
one competency question (CQ). A CQ is considered answered if the query
returns at least one result row against the merged ontology.

Test modes
----------
Default (rdflib / schema-only):
    Most CQs xfail because there is no instance data.  Only CQs already
    marked ``# STRICT`` in the .rq file are hard assertions.

GraphDB live-data mode (--graphdb-url):
    Queries run against real vessel repositories.  Same xfail/STRICT logic.

GraphDB test-repo mode (--graphdb-url + --graphdb-test-repo):
    Queries run against the synthetic test repository loaded from
    tests/data/twinship-test-instances.ttl.  In this mode every CQ is
    treated as a strict assertion UNLESS the .rq file contains the comment
    ``# NOT-YET-MODELLED``.

Reports
-------
After each run, two outputs are written to reports/ (gitignored):
    reports/cq-report.html        — HTML table with all CQs, status, timing,
                                    and collapsible sample result rows
    reports/cq-results/<cq>.csv  — full result rows for each CQ

To run:
    # schema-only
    uv run pytest tests/test_competency_questions.py -v
    # live GraphDB
    uv run pytest tests/test_competency_questions.py -v \\
        --graphdb-url http://localhost:7200
    # test-repo (strict)
    uv run pytest tests/test_competency_questions.py -v \\
        --graphdb-url http://localhost:7200 --graphdb-test-repo vessel-test
"""

import concurrent.futures
import time
from pathlib import Path
from typing import Any

import pytest

from conftest import CQRecord, CQResultCollector

CQ_DIR = Path(__file__).parent / "competency"
_QUERY_TIMEOUT_S = 30

# Collect all .rq files; skip gracefully if the directory is empty.
cq_files = sorted(CQ_DIR.glob("*.rq")) if CQ_DIR.exists() else []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_cq_description(query_text: str) -> str:
    """Return the human-readable question from the first '# CQ-NN —' line."""
    for line in query_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# CQ-"):
            return stripped[2:].strip()
    return ""


def _normalise_rows(raw: Any) -> tuple[list[str], list[list[str]]]:
    """Convert rdflib Result or GraphDB list-of-dicts to (columns, rows).

    Both return types are supported:
    - rdflib Result: has .vars attribute; rows are tuples of rdflib terms.
    - GraphDB list:  rows are dicts mapping var name to SPARQL JSON binding.
    """
    if hasattr(raw, "vars"):
        # rdflib Result
        cols = [str(v) for v in (raw.vars or [])]
        rows = [
            [str(v) if v is not None else "" for v in row]
            for row in raw
        ]
    else:
        # GraphDB: list of dicts
        raw_list = list(raw)
        if not raw_list:
            return [], []
        cols = list(raw_list[0].keys())
        rows = [
            [row.get(c, {}).get("value", "") for c in cols]
            for row in raw_list
        ]
    return cols, rows


def _run_query(
    graph: Any, sparql: str
) -> tuple[list[str], list[list[str]], float, str]:
    """Execute sparql against graph with a timeout.

    Returns (columns, rows, duration_ms, query_status) where query_status is
    one of: "OK" | "TIMEOUT" | "ERROR: <message>".
    """
    t0 = time.monotonic()

    def _do() -> tuple[list[str], list[list[str]]]:
        return _normalise_rows(graph.query(sparql))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_do)
        try:
            cols, rows = future.result(timeout=_QUERY_TIMEOUT_S)
            return cols, rows, (time.monotonic() - t0) * 1000, "OK"
        except concurrent.futures.TimeoutError:
            return [], [], (time.monotonic() - t0) * 1000, "TIMEOUT"
        except Exception as exc:  # noqa: BLE001
            return [], [], (time.monotonic() - t0) * 1000, f"ERROR: {exc}"


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rq_file", cq_files, ids=[f.stem for f in cq_files])
def test_competency_question(
    rq_file: Path,
    graph: Any,
    test_repo_mode: bool,
    cq_collector: CQResultCollector,
) -> None:
    """Execute a CQ query, record results to disk, and assert coverage.

    Strictness rules (in order of precedence):
    1. ``# NOT-YET-MODELLED`` → always xfail; required ontology feature missing.
    2. test-repo mode (--graphdb-test-repo) → strict unless rule 1.
    3. ``# STRICT`` in .rq file → strict in any mode.
    4. Otherwise → xfail (reporting-only).
    """
    query_text = rq_file.read_text(encoding="utf-8")
    description = _extract_cq_description(query_text)
    not_yet_modelled = "# NOT-YET-MODELLED" in query_text
    explicitly_strict = "# STRICT" in query_text
    is_strict = (explicitly_strict or test_repo_mode) and not not_yet_modelled

    cols, rows, duration_ms, query_status = _run_query(graph, query_text)

    # Determine report status (before any pytest.xfail / assert)
    if query_status == "TIMEOUT":
        status = "TIMEOUT"
        error_msg: str | None = f"Timed out after {_QUERY_TIMEOUT_S}s"
    elif query_status.startswith("ERROR"):
        status = "ERROR"
        error_msg = query_status[7:]  # strip "ERROR: "
    elif len(rows) > 0:
        status = "PASS"
        error_msg = None
    elif is_strict:
        status = "FAIL"
        error_msg = None
    else:
        status = "XFAIL"
        error_msg = None

    cq_collector.add(CQRecord(
        cq_id=rq_file.stem,
        description=description,
        status=status,
        row_count=len(rows),
        duration_ms=duration_ms,
        columns=cols,
        rows=rows,
        error_msg=error_msg,
    ))

    # Apply pytest verdict
    if query_status == "TIMEOUT":
        pytest.fail(
            f"CQ '{rq_file.stem}' timed out after {_QUERY_TIMEOUT_S}s"
        )
    elif query_status.startswith("ERROR"):
        raise RuntimeError(query_status)
    elif is_strict:
        assert len(rows) > 0, (
            f"Competency question '{rq_file.stem}' returned no results — "
            "ontology does not yet cover this CQ."
        )
    else:
        if len(rows) == 0:
            pytest.xfail(
                f"Competency question '{rq_file.stem}' returned no results — "
                "ontology does not yet fully cover this CQ (reporting-only)."
            )
