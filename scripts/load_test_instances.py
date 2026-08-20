#!/usr/bin/env python3
"""
Load TwinShip dummy test instances into a GraphDB test repository.

Creates the repository if it does not already exist, then POSTs the
synthetic test-data TTL from tests/data/twinship-test-instances.ttl
as the default graph.

Usage:
    uv run python scripts/load_test_instances.py

Options (environment variables):
    GRAPHDB_URL          GraphDB base URL (default: http://localhost:7200)
    GRAPHDB_TEST_REPO    Repository ID    (default: vessel-test)
    GRAPHDB_TOKEN        Bearer token     (optional; used if set)
    KEYCLOAK_CLIENT_ID   }  Used to fetch a token via Keycloak client-
    KEYCLOAK_CLIENT_SECRET }  credentials flow when no GRAPHDB_TOKEN is set.
    KEYCLOAK_URL         Keycloak base URL (default: http://localhost:8080)
    KEYCLOAK_REALM       Realm name        (default: twinship)

The script is idempotent: re-running it replaces the existing triples in
the default graph of the test repository.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GRAPHDB_URL = os.environ.get("GRAPHDB_URL", "http://localhost:7200").rstrip("/")
TEST_REPO = os.environ.get("GRAPHDB_TEST_REPO", "vessel-test")
TTL_PATH = Path(__file__).parent.parent / "tests" / "data" / "twinship-test-instances.ttl"

# ---------------------------------------------------------------------------
# Auth helpers (shared with conftest.py logic)
# ---------------------------------------------------------------------------


def _fetch_keycloak_token() -> str | None:
    """Obtain a bearer token via Keycloak client credentials flow."""
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


def get_token() -> str | None:
    env_token = os.environ.get("GRAPHDB_TOKEN", "")
    if env_token:
        return env_token
    return _fetch_keycloak_token()


# ---------------------------------------------------------------------------
# GraphDB REST helpers
# ---------------------------------------------------------------------------


def _request(url: str, method: str, data: bytes | None = None,
             content_type: str | None = None, token: str | None = None,
             accept: str | None = None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=data, method=method)
    if content_type:
        req.add_header("Content-Type", content_type)
    if accept:
        req.add_header("Accept", accept)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def repo_exists(token: str | None) -> bool:
    url = f"{GRAPHDB_URL}/rest/repositories/{TEST_REPO}"
    code, _ = _request(url, "GET", token=token, accept="application/json")
    return code == 200


def create_repo(token: str | None) -> None:
    """Create a basic GraphDB repository using the REST API."""
    url = f"{GRAPHDB_URL}/rest/repositories"
    config = {
        "id": TEST_REPO,
        "title": "TwinShip synthetic test data",
        "type": "graphdb",
        "params": {
            "repositoryType": {"name": "repositoryType", "label": "Repository type", "value": "file-repository"},
            "ruleset": {"name": "ruleset", "label": "Ruleset", "value": "rdfsplus-optimized"},
            "storageFolder": {"name": "storageFolder", "label": "Storage folder", "value": "storage"},
        },
    }
    body = json.dumps(config).encode()
    code, resp = _request(url, "POST", data=body,
                          content_type="application/json", token=token)
    if code not in (200, 201):
        raise RuntimeError(
            f"Failed to create repository '{TEST_REPO}': HTTP {code} — {resp.decode()[:200]}"
        )
    print(f"  Created repository '{TEST_REPO}'.")


def clear_default_graph(token: str | None) -> None:
    """DELETE the default graph to allow a clean reload."""
    url = f"{GRAPHDB_URL}/repositories/{TEST_REPO}/statements"
    code, _ = _request(url, "DELETE", token=token)
    if code not in (200, 204):
        print(f"  Warning: could not clear default graph (HTTP {code}) — proceeding anyway.")


def load_ttl(ttl_path: Path, token: str | None) -> None:
    """PUT the TTL file into the default graph."""
    url = f"{GRAPHDB_URL}/repositories/{TEST_REPO}/statements"
    data = ttl_path.read_bytes()
    code, resp = _request(url, "PUT", data=data,
                          content_type="application/x-turtle", token=token)
    if code not in (200, 204):
        raise RuntimeError(
            f"Failed to upload triples: HTTP {code} — {resp.decode()[:200]}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    if not TTL_PATH.exists():
        print(f"ERROR: test-data file not found: {TTL_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"GraphDB:   {GRAPHDB_URL}")
    print(f"Repo:      {TEST_REPO}")
    print(f"Data file: {TTL_PATH}")
    print()

    token = get_token()
    if token:
        print("  Auth: bearer token obtained.")
    else:
        print("  Auth: no token (anonymous access).")

    # Create repository if needed
    if not repo_exists(token):
        print(f"  Repository '{TEST_REPO}' not found — creating…")
        create_repo(token)
    else:
        print(f"  Repository '{TEST_REPO}' already exists.")
        print("  Clearing existing triples from default graph…")
        clear_default_graph(token)

    # Load TTL
    print(f"  Loading {TTL_PATH.name}…")
    load_ttl(TTL_PATH, token)
    print(f"  Done. Test data loaded into '{TEST_REPO}'.")
    print()
    print("Run CQ tests against the test repository:")
    print(
        f"  uv run pytest tests/ --graphdb-url {GRAPHDB_URL} "
        f"--graphdb-test-repo {TEST_REPO} -v"
    )


if __name__ == "__main__":
    main()
