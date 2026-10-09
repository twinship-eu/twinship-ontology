# TwinShip Ontology - Server Deployment Guide

This guide describes how to deploy the generated ontology website and configure the
necessary server-side redirects for proper IRI resolution.

## Hosting Overview

The TwinShip ontology uses two domains:

| Domain | Purpose |
|--------|---------|
| `twin-ship.eu` | Main project website; ontology namespace (`https://twin-ship.eu/twinship#`) |
| `ontology.twin-ship.eu` | Hosts the generated documentation and WebVOWL visualization |

The ontology namespace (`https://twin-ship.eu/twinship#`) is the permanent, canonical
identifier for all TwinShip classes and properties. This namespace must not change, as it
is embedded in the ontology files and in any data that references them.

## Deploying the Website

The generated website lives in `docs/website/` after running the build pipeline:

```bash
./scripts/generate_website.sh --verbose
```

Deploy the contents of `docs/website/documentation/` to the web root of
`ontology.twin-ship.eu`. The directory structure should be:

```
ontology.twin-ship.eu/
├── index-en.html                 # WIDOCO documentation (main)
├── index.html                    # Redirect to index-en.html
├── ontology.ttl                  # Turtle serialization
├── ontology.owl                  # RDF/XML serialization
├── ontology.nt                   # N-Triples serialization
├── ontology.jsonld               # JSON-LD serialization
├── resources/                    # CSS, JS assets
├── provenance/                   # Provenance documentation
└── webvowl/
    ├── index.html                # WebVOWL visualization
    ├── data/ontology.json        # WebVOWL graph data
    ├── css/                      # WebVOWL styles
    └── js/                       # WebVOWL scripts
```

## Making Entity Links Resolve

WebVOWL's "Selection Details" panel links each class or property to its ontology IRI,
e.g. `https://twin-ship.eu/twinship#EngineSystem`. Without server-side redirects on the
`twin-ship.eu` domain, these links lead to a 404. There are two ways to handle this:

| Option | Approach | Status |
|--------|----------|--------|
| A | Server-side 303 redirect on `twin-ship.eu` (plus a client-side hash rewrite, see below) | Not deployed; requires control of `twin-ship.eu` |
| B | Build step that patches WebVOWL so entity links point to the WIDOCO docs directly | **Currently used** |

**Option B (current).** `scripts/patch_webvowl_links.py` runs as step 4.7 of
`generate_website.sh` and patches `webvowl/js/webvowl.app.js`. Links to
`https://twin-ship.eu/twinship#X` become `../index-en.html#https://twin-ship.eu/twinship#X`,
which scrolls to the entity in the WIDOCO docs. The link text and tooltip still show the
IRI. This does not make the IRI itself dereferenceable for external tools; that needs
Option A.

**Option A (not yet in use)** is described in the rest of this document. It is the
standard Linked Data solution and also makes the IRIs dereferenceable for RDF tools.

The standard solution in the Semantic Web is **HTTP content negotiation**: the server at
the namespace domain redirects to the appropriate documentation depending on what the
client requests.

- **Browsers** (requesting HTML) should be redirected to the human-readable WIDOCO docs.
- **Semantic Web tools** (requesting RDF) should be redirected to the machine-readable
  ontology file.

This follows the [W3C Best Practice for Publishing Linked Data](https://www.w3.org/TR/swbp-vocab-pub/)
and the [Cool URIs for the Semantic Web](https://www.w3.org/TR/cooluris/) recommendations.

## Redirect Configuration (Option A)

The redirects must be configured on the **`twin-ship.eu`** server (not on `ontology.twin-ship.eu`).

### Nginx

```nginx
server {
    server_name twin-ship.eu www.twin-ship.eu;

    # Ontology namespace content negotiation
    location /twinship {
        # Serve Turtle to RDF clients
        if ($http_accept ~* "text/turtle") {
            return 303 https://ontology.twin-ship.eu/ontology.ttl;
        }

        # Serve RDF/XML to RDF clients
        if ($http_accept ~* "application/rdf\+xml") {
            return 303 https://ontology.twin-ship.eu/ontology.owl;
        }

        # Serve JSON-LD to JSON-LD clients
        if ($http_accept ~* "application/ld\+json") {
            return 303 https://ontology.twin-ship.eu/ontology.jsonld;
        }

        # Serve N-Triples to N-Triples clients
        if ($http_accept ~* "application/n-triples") {
            return 303 https://ontology.twin-ship.eu/ontology.nt;
        }

        # Default: redirect browsers to human-readable documentation
        return 303 https://ontology.twin-ship.eu/index-en.html;
    }

    # ... other server configuration ...
}
```

### Apache (.htaccess)

```apache
RewriteEngine On

# Ontology namespace content negotiation
# Turtle
RewriteCond %{HTTP_ACCEPT} text/turtle
RewriteRule ^twinship(.*)$ https://ontology.twin-ship.eu/ontology.ttl [R=303,L]

# RDF/XML
RewriteCond %{HTTP_ACCEPT} application/rdf\+xml
RewriteRule ^twinship(.*)$ https://ontology.twin-ship.eu/ontology.owl [R=303,L]

# JSON-LD
RewriteCond %{HTTP_ACCEPT} application/ld\+json
RewriteRule ^twinship(.*)$ https://ontology.twin-ship.eu/ontology.jsonld [R=303,L]

# N-Triples
RewriteCond %{HTTP_ACCEPT} application/n-triples
RewriteRule ^twinship(.*)$ https://ontology.twin-ship.eu/ontology.nt [R=303,L]

# Default: HTML documentation
RewriteRule ^twinship(.*)$ https://ontology.twin-ship.eu/index-en.html [R=303,L]
```

## How Fragment Identifiers Work

Entity IRIs use a hash namespace: `https://twin-ship.eu/twinship#EngineSystem`. The
`#EngineSystem` part is a **fragment identifier** — the browser never sends it to the
server. Instead:

1. Browser requests `https://twin-ship.eu/twinship`
2. Server responds with `303 See Other` → `https://ontology.twin-ship.eu/index-en.html`
3. Browser follows the redirect and re-appends the original fragment only:
   `https://ontology.twin-ship.eu/index-en.html#EngineSystem`
4. WIDOCO anchors use the **full IRI** as element id
   (`id="https://twin-ship.eu/twinship#EngineSystem"`), so `#EngineSystem` matches nothing
   and the page opens at the top without scrolling.

A single redirect rule therefore handles all entities, but a small client-side script on
`index-en.html` is also needed for Option A to scroll correctly: on load and `hashchange`,
rewrite a short hash `#Name` to `#https://twin-ship.eu/twinship#Name`. This script is
**not implemented yet** (not needed while Option B is used).

## Verifying the Setup

After configuring redirects, verify with `curl`:

```bash
# HTML redirect (browser behavior)
curl -sI -H "Accept: text/html" https://twin-ship.eu/twinship
# Expected: 303 with Location: https://ontology.twin-ship.eu/index-en.html

# Turtle redirect (RDF tool behavior)
curl -sI -H "Accept: text/turtle" https://twin-ship.eu/twinship
# Expected: 303 with Location: https://ontology.twin-ship.eu/ontology.ttl

# RDF/XML redirect
curl -sI -H "Accept: application/rdf+xml" https://twin-ship.eu/twinship
# Expected: 303 with Location: https://ontology.twin-ship.eu/ontology.owl
```

## Notes

- **Use 303 (See Other)**, not 301 or 302. The 303 status code is the correct HTTP
  response for ontology IRIs per Linked Data conventions — it indicates that the requested
  resource is described by the document at the redirect target.
- The `/twinship/base` and `/twinship/core` paths (ontology-level IRIs without the `#`)
  could also benefit from similar redirects if external tools attempt to dereference them.
- CORS headers may be needed on `ontology.twin-ship.eu` if RDF tools fetch ontology files
  via JavaScript (e.g., `Access-Control-Allow-Origin: *`).
