"""
Pytest configuration for TwinShip ontology tests.

Default mode: loads the merged ontology from build/twinship-core-complete.ttl
via rdflib (schema-only; most CQs xfail for lack of instance data).

GraphDB mode: when --graphdb-url is set, queries are sent to a live GraphDB
instance running the twinship-data-pipeline stack (docker-compose up). Results
are combined across all configured vessel repositories.

Test-repo mode: when --graphdb-test-repo is set (together with --graphdb-url),
queries are run against a single dedicated test repository loaded with the
synthetic dummy data from tests/data/twinship-test-instances.ttl.  In this
mode all CQs whose test data covers them are treated as strict assertions
(failures are hard errors, not xfail).  Use this mode for CI validation of
the full ontology against known instance data.  Load the test data first:

    uv run python scripts/load_test_instances.py

Usage — rdflib (default):
    uv run pytest tests/

Usage — GraphDB with instance data:
    uv run pytest tests/ --graphdb-url http://localhost:7200

Usage — GraphDB test-repo (strict, synthetic data):
    uv run pytest tests/ --graphdb-url http://localhost:7200 \\
                         --graphdb-test-repo vessel-test

Authentication (GraphDB uses Keycloak OpenID — provide one of):
    # Pre-acquired bearer token
    GRAPHDB_TOKEN=<token> uv run pytest tests/ --graphdb-url http://localhost:7200

    # Keycloak client credentials (token fetched automatically)
    KEYCLOAK_CLIENT_ID=<your-client-id> \\
    KEYCLOAK_CLIENT_SECRET=<your-client-secret> \\
    uv run pytest tests/ --graphdb-url http://localhost:7200

Repositories queried (override with --graphdb-repos):
    vessel-roro, vessel-ropax, vessel-tanker, vessel-futuristic
    (defaults are generic placeholders — replace with your actual GraphDB repo IDs)
"""

import csv
import dataclasses
import html as _html
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

import pytest
from pathlib import Path
from rdflib import ConjunctiveGraph

ONTOLOGY_PATH = Path(__file__).parent.parent / "build" / "twinship-core-complete.ttl"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
CQ_RESULTS_DIR = REPORTS_DIR / "cq-results"

_QUERY_TIMEOUT_S = 30

# Generic placeholder names — override with --graphdb-repos to match
# the actual repository IDs in your GraphDB instance.
_DEFAULT_REPOS = ["vessel-roro", "vessel-ropax", "vessel-tanker", "vessel-futuristic"]

# ---------------------------------------------------------------------------
# CQ result record and collector
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class CQRecord:
    cq_id: str            # e.g. "cq01_vessels_by_fleet_and_type"
    description: str      # human-readable first comment line from .rq file
    status: str           # PASS | FAIL | XFAIL | ERROR | TIMEOUT
    row_count: int
    duration_ms: float
    columns: list         # result variable names
    rows: list            # all result rows as list[list[str]]
    error_msg: str | None


class CQResultCollector:
    """Accumulates CQ results during a test session and writes reports at the end."""

    _MAX_HTML_ROWS = 10   # rows shown inline in the HTML report

    def __init__(self) -> None:
        self._records: list[CQRecord] = []

    def add(self, record: CQRecord) -> None:
        self._records.append(record)

    @property
    def records(self) -> list[CQRecord]:
        return sorted(self._records, key=lambda r: r.cq_id)

    def write_reports(self, run_mode: str) -> None:
        if not self._records:
            return
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        CQ_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self._write_csvs()
        html_path = self._write_html(run_mode)
        print(f"\n[conftest] Reports written to {REPORTS_DIR}/")
        print(f"           HTML: {html_path.name}")
        print(f"           CSVs: cq-results/ ({len(self._records)} files)")

    # -- CSV -----------------------------------------------------------------

    def _write_csvs(self) -> None:
        for rec in self._records:
            csv_path = CQ_RESULTS_DIR / f"{rec.cq_id}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if rec.columns:
                    writer.writerow(rec.columns)
                    writer.writerows(rec.rows)
                elif rec.error_msg:
                    writer.writerow(["error"])
                    writer.writerow([rec.error_msg])

    # -- HTML ----------------------------------------------------------------

    def _write_html(self, run_mode: str) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        counts: dict[str, int] = {
            s: sum(1 for r in self._records if r.status == s)
            for s in ("PASS", "FAIL", "XFAIL", "TIMEOUT", "ERROR")
        }
        html_path = REPORTS_DIR / "cq-report.html"
        html_path.write_text(
            _render_html(self.records, run_mode, timestamp, counts,
                         self._MAX_HTML_ROWS),
            encoding="utf-8",
        )
        return html_path


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

_STATUS_CSS = {
    "PASS":    "badge-pass",
    "FAIL":    "badge-fail",
    "XFAIL":   "badge-xfail",
    "TIMEOUT": "badge-timeout",
    "ERROR":   "badge-error",
}

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, -apple-system, sans-serif; font-size: 14px;
       color: #1e293b; background: #f8fafc; padding: 1.5rem; }
h1 { font-size: 1.35rem; margin-bottom: .25rem; }
.meta { margin-bottom: 1.5rem; color: #64748b; font-size: .9rem; }
.meta p { margin-bottom: .5rem; }
.badges { display: flex; gap: .5rem; flex-wrap: wrap; }
.badge { padding: .2rem .75rem; border-radius: 999px; font-size: .75rem;
         font-weight: 700; white-space: nowrap; }
.badge-pass    { background: #22c55e; color: #fff; }
.badge-fail    { background: #ef4444; color: #fff; }
.badge-xfail   { background: #f59e0b; color: #fff; }
.badge-timeout { background: #f97316; color: #fff; }
.badge-error   { background: #dc2626; color: #fff; }
table.main { width: 100%; border-collapse: collapse; background: #fff;
             box-shadow: 0 1px 4px rgba(0,0,0,.1); border-radius: .5rem;
             overflow: hidden; }
table.main thead th { background: #1e293b; color: #e2e8f0; padding: .55rem .8rem;
                      text-align: left; font-weight: 600; white-space: nowrap; }
table.main tbody tr:nth-child(even) { background: #f8fafc; }
table.main tbody tr:hover { background: #e0f2fe; }
table.main td { padding: .45rem .8rem; vertical-align: top;
                border-bottom: 1px solid #e2e8f0; }
.cq-id { font-family: ui-monospace, monospace; font-size: .8rem;
          white-space: nowrap; }
.desc { max-width: 30rem; line-height: 1.4; }
.dur  { white-space: nowrap; color: #94a3b8; font-size: .85rem;
        text-align: right; }
.row-count { text-align: center; font-weight: 700; }
details > summary { cursor: pointer; color: #2563eb; font-size: .82rem;
                    list-style: none; }
details[open] > summary { color: #7c3aed; }
table.res { margin-top: .4rem; font-size: .75rem; border-collapse: collapse;
            max-width: 100%; display: block; overflow-x: auto; }
table.res th { background: #475569; color: #f1f5f9; padding: .2rem .5rem;
               white-space: nowrap; }
table.res td { padding: .2rem .5rem; border-bottom: 1px solid #e2e8f0;
               max-width: 22rem; overflow: hidden; text-overflow: ellipsis;
               white-space: nowrap; }
.err-msg { color: #ef4444; font-family: ui-monospace, monospace;
           font-size: .78rem; word-break: break-all; }
"""


def _render_html(records: list[CQRecord], run_mode: str, timestamp: str,
                 counts: dict[str, int], max_html_rows: int) -> str:
    total = len(records)

    # Summary badges
    badge_parts = []
    for status, css in _STATUS_CSS.items():
        n = counts.get(status, 0)
        if n:
            badge_parts.append(
                f'<span class="badge {css}">{status} {n}</span>'
            )

    # Table rows
    row_parts = []
    for rec in records:
        css = _STATUS_CSS.get(rec.status, "badge-error")
        badge = f'<span class="badge {css}">{_html.escape(rec.status)}</span>'
        dur = f"{rec.duration_ms:.1f}" if rec.duration_ms > 0 else "—"

        # Result cell
        if rec.error_msg:
            result_cell = (
                f'<span class="err-msg">'
                f'{_html.escape(rec.error_msg[:200])}</span>'
            )
        elif rec.columns and rec.rows:
            shown = rec.rows[:max_html_rows]
            more = rec.row_count - len(shown)
            more_note = f" (+ {more} more, see CSV)" if more > 0 else ""
            th = "".join(
                f"<th>{_html.escape(str(c))}</th>" for c in rec.columns
            )
            trs = "".join(
                "<tr>"
                + "".join(
                    f'<td title="{_html.escape(str(v))}">'
                    f'{_html.escape(str(v)[:80])}</td>'
                    for v in row
                )
                + "</tr>"
                for row in shown
            )
            result_cell = (
                f"<details><summary>"
                f"Show {len(shown)} row{'s' if len(shown) != 1 else ''}"
                f"{more_note}</summary>"
                f'<table class="res"><thead><tr>{th}</tr></thead>'
                f"<tbody>{trs}</tbody></table></details>"
            )
        elif rec.status == "XFAIL":
            result_cell = '<span style="color:#94a3b8">no rows (expected)</span>'
        else:
            result_cell = '<span style="color:#94a3b8">—</span>'

        row_parts.append(
            "<tr>"
            f'<td class="cq-id">{_html.escape(rec.cq_id)}</td>'
            f'<td class="desc">{_html.escape(rec.description)}</td>'
            f"<td>{badge}</td>"
            f'<td class="row-count">{rec.row_count if rec.row_count > 0 else "—"}</td>'
            f'<td class="dur">{dur}</td>'
            f"<td>{result_cell}</td>"
            "</tr>"
        )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>TwinShip CQ Report</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<h1>TwinShip — Competency Question Test Report</h1>\n"
        '<div class="meta">\n'
        f"  <p>Generated: {_html.escape(timestamp)}"
        f" &nbsp;|&nbsp; Mode: <strong>{_html.escape(run_mode)}</strong>"
        f" &nbsp;|&nbsp; Total CQs: {total}</p>\n"
        '  <div class="badges">\n    '
        + "\n    ".join(badge_parts)
        + "\n  </div>\n</div>\n"
        '<table class="main">\n'
        "<thead><tr>"
        "<th>CQ</th><th>Description</th><th>Status</th>"
        "<th>Rows</th><th>ms</th><th>Results</th>"
        "</tr></thead>\n"
        "<tbody>\n"
        + "\n".join(row_parts)
        + "\n</tbody>\n</table>\n"
        "</body>\n</html>\n"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_run_mode(config: pytest.Config) -> str:
    graphdb_url = config.getoption("--graphdb-url", default=None)
    test_repo = config.getoption("--graphdb-test-repo", default=None)
    if test_repo and graphdb_url:
        return f"GraphDB test-repo — {test_repo} (strict)"
    if graphdb_url:
        repos = config.getoption("--graphdb-repos", default="")
        return f"GraphDB — {graphdb_url} | repos: {repos}"
    return "rdflib (schema-only)"


# ---------------------------------------------------------------------------
# Pytest hooks and fixtures
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Create the result collector early so it is available for all tests."""
    config._cq_collector = CQResultCollector()


def pytest_sessionfinish(session: pytest.Session, exitstatus: object) -> None:
    """Write HTML and CSV reports after all tests have run."""
    collector: CQResultCollector | None = getattr(
        session.config, "_cq_collector", None
    )
    if collector is not None:
        run_mode = _get_run_mode(session.config)
        collector.write_reports(run_mode)


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--graphdb-url",
        action="store",
        default=None,
        metavar="URL",
        help="GraphDB base URL (e.g. http://localhost:7200). "
             "When set, CQ tests run against live GraphDB with instance data.",
    )
    parser.addoption(
        "--graphdb-repos",
        action="store",
        default=",".join(_DEFAULT_REPOS),
        metavar="REPOS",
        help="Comma-separated GraphDB repository IDs to query. "
             "Must match the actual repository IDs in your GraphDB instance. "
             f"Defaults to generic placeholders: {', '.join(_DEFAULT_REPOS)}.",
    )
    parser.addoption(
        "--graphdb-test-repo",
        action="store",
        default=None,
        metavar="REPO",
        help="GraphDB repository ID for the synthetic test data "
             "(e.g. vessel-test). Requires --graphdb-url. When set, "
             "only this repository is queried and all CQs that the test data "
             "covers are treated as strict assertions (hard failures). "
             "Load the test data first with: "
             "uv run python scripts/load_test_instances.py",
    )


# ---------------------------------------------------------------------------
# GraphDB federated SPARQL client
# ---------------------------------------------------------------------------


class GraphDBFederatedSparql:
    """Execute SPARQL SELECT queries across multiple GraphDB repositories.

    Provides the same ``.query(sparql)`` interface as an rdflib graph so that
    ``test_competency_questions.py`` works unchanged in both modes.
    """

    def __init__(self, base_url: str, repo_ids: list[str], token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.repo_ids = repo_ids
        self._token = token

    # -- auth ----------------------------------------------------------------

    @staticmethod
    def _fetch_keycloak_token() -> str | None:
        """Try to obtain a bearer token via Keycloak client credentials flow.

        Reads KEYCLOAK_URL (default http://localhost:8080), KEYCLOAK_REALM
        (default twinship), KEYCLOAK_CLIENT_ID, KEYCLOAK_CLIENT_SECRET from
        the environment.  Returns None when credentials are not configured.
        """
        client_id = os.environ.get("KEYCLOAK_CLIENT_ID", "")
        client_secret = os.environ.get("KEYCLOAK_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            return None

        keycloak_url = os.environ.get("KEYCLOAK_URL", "http://localhost:8080").rstrip("/")
        realm = os.environ.get("KEYCLOAK_REALM", "twinship")
        token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"

        body = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }).encode()
        req = urllib.request.Request(token_url, data=body, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode()).get("access_token")
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Could not reach Keycloak at {token_url}: {exc}. "
                "Is docker-compose running?"
            ) from exc

    def _get_token(self) -> str | None:
        """Return a bearer token, acquiring one from Keycloak if needed."""
        if self._token:
            return self._token
        # Try env var first, then Keycloak credentials flow
        env_token = os.environ.get("GRAPHDB_TOKEN", "")
        if env_token:
            return env_token
        return self._fetch_keycloak_token()

    # -- query ---------------------------------------------------------------

    def _query_repo(self, repo_id: str, sparql: str, token: str | None) -> list[dict]:
        """POST a SPARQL SELECT to one repository; return the JSON bindings list."""
        url = f"{self.base_url}/repositories/{repo_id}"
        data = urllib.parse.urlencode({"query": sparql}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Accept", "application/sparql-results+json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
        return body.get("results", {}).get("bindings", [])

    def query(self, sparql: str) -> list[dict]:
        """Query all repositories and return combined, deduplicated bindings."""
        token = self._get_token()
        seen: set[str] = set()
        combined: list[dict] = []
        for repo_id in self.repo_ids:
            try:
                bindings = self._query_repo(repo_id, sparql, token)
            except urllib.error.HTTPError as exc:
                print(f"\n  [graphdb:{repo_id}] HTTP {exc.code} — skipping")
                continue
            except urllib.error.URLError as exc:
                print(f"\n  [graphdb:{repo_id}] {exc} — skipping")
                continue
            for row in bindings:
                # Deduplicate by serialising sorted (key, value) pairs
                key = str(sorted((k, v.get("value", "")) for k, v in row.items()))
                if key not in seen:
                    seen.add(key)
                    combined.append(row)
        return combined


# ---------------------------------------------------------------------------
# Session fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_repo_mode(request: pytest.FixtureRequest) -> bool:
    """True when --graphdb-test-repo is provided.

    Test functions use this to promote CQs from xfail to strict assertions
    when running against the synthetic test repository.
    """
    return request.config.getoption("--graphdb-test-repo") is not None


@pytest.fixture(scope="session")
def cq_collector(request: pytest.FixtureRequest) -> CQResultCollector:
    """Session-scoped collector that stores per-CQ results for reporting."""
    return request.config._cq_collector


@pytest.fixture(scope="session")
def graph(request: pytest.FixtureRequest):
    """Return a query-capable object for competency question tests.

    - Without --graphdb-url: parse the merged TTL via rdflib (schema only).
    - With --graphdb-url only: return a GraphDBFederatedSparql client that
      queries all configured vessel repositories with live instance data.
    - With --graphdb-url and --graphdb-test-repo: query only the single
      synthetic test repository (vessel-test or similar).  All CQs with
      test-data coverage are treated as strict assertions.
    """
    graphdb_url: str | None = request.config.getoption("--graphdb-url")
    test_repo: str | None = request.config.getoption("--graphdb-test-repo")

    if graphdb_url and test_repo:
        print(
            f"\n[conftest] GraphDB test-repo mode — {graphdb_url} | repo: {test_repo}"
        )
        return GraphDBFederatedSparql(base_url=graphdb_url, repo_ids=[test_repo])

    if graphdb_url:
        repos_opt: str = request.config.getoption("--graphdb-repos")
        repo_ids = [r.strip() for r in repos_opt.split(",") if r.strip()]
        print(
            f"\n[conftest] GraphDB mode — {graphdb_url} | repos: {', '.join(repo_ids)}"
        )
        return GraphDBFederatedSparql(base_url=graphdb_url, repo_ids=repo_ids)

    # Default: rdflib in-memory graph (schema only)
    if not ONTOLOGY_PATH.exists():
        pytest.skip(
            f"Merged ontology not found at {ONTOLOGY_PATH}. "
            "Run 'uv run python scripts/merge_modules.py --auto' first."
        )
    g = ConjunctiveGraph()
    g.parse(str(ONTOLOGY_PATH), format="turtle")
    return g
