"""
Pytest configuration for TwinShip ontology tests.

Default mode: loads the merged ontology from build/twinship-core-complete.ttl
via rdflib (schema-only; most CQs xfail for lack of instance data).

GraphDB mode: when --graphdb-url is set, queries are sent to a live GraphDB
instance running the twinship-data-pipeline stack (docker-compose up). Results
are combined across all configured vessel repositories.

Usage — rdflib (default):
    uv run pytest tests/

Usage — GraphDB with instance data:
    uv run pytest tests/ --graphdb-url http://localhost:7200

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

import json
import os
import urllib.error
import urllib.parse
import urllib.request

import pytest
from pathlib import Path
from rdflib import ConjunctiveGraph

ONTOLOGY_PATH = Path(__file__).parent.parent / "build" / "twinship-core-complete.ttl"

# Generic placeholder names — override with --graphdb-repos to match
# the actual repository IDs in your GraphDB instance.
_DEFAULT_REPOS = ["vessel-roro", "vessel-ropax", "vessel-tanker", "vessel-futuristic"]


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
def graph(request: pytest.FixtureRequest):
    """Return a query-capable object for competency question tests.

    - Without --graphdb-url: parse the merged TTL via rdflib (schema only).
    - With --graphdb-url: return a GraphDBFederatedSparql client that queries
      all configured vessel repositories with live instance data.
    """
    graphdb_url: str | None = request.config.getoption("--graphdb-url")

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
