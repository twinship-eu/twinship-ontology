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

Deploy the contents of `docs/website/` to the web root of `ontology.twin-ship.eu`. The
directory structure should be:

```
ontology.twin-ship.eu/
├── index.html                    # Landing page
└── documentation/
    ├── index-en.html             # WIDOCO documentation (main)
    ├── index.html                # Redirect to index-en.html
    ├── ontology.ttl              # Turtle serialization
    ├── ontology.owl              # RDF/XML serialization
    ├── ontology.nt               # N-Triples serialization
    ├── ontology.jsonld            # JSON-LD serialization
    ├── resources/                # CSS, JS assets
    ├── provenance/               # Provenance documentation
    └── webvowl/
        ├── index.html            # WebVOWL visualization
        ├── data/ontology.json    # WebVOWL graph data
        ├── css/                  # WebVOWL styles
        └── js/                   # WebVOWL scripts
```

## Why Server-Side Redirects Are Needed

When users interact with the documentation — particularly in WebVOWL — clicking a class
or property opens a link to its ontology IRI, e.g.
`https://twin-ship.eu/twinship#EngineSystem`. This is correct Linked Data behavior: the
IRI is the entity's permanent identifier. However, without server-side redirects on the
`twin-ship.eu` domain, these links lead to a 404.

The standard solution in the Semantic Web is **HTTP content negotiation**: the server at
the namespace domain redirects to the appropriate documentation depending on what the
client requests.

- **Browsers** (requesting HTML) should be redirected to the human-readable WIDOCO docs.
- **Semantic Web tools** (requesting RDF) should be redirected to the machine-readable
  ontology file.

This follows the [W3C Best Practice for Publishing Linked Data](https://www.w3.org/TR/swbp-vocab-pub/)
and the [Cool URIs for the Semantic Web](https://www.w3.org/TR/cooluris/) recommendations.

## Redirect Configuration

The redirects must be configured on the **`twin-ship.eu`** server (not on `ontology.twin-ship.eu`).

### Nginx

```nginx
server {
    server_name twin-ship.eu www.twin-ship.eu;

    # Ontology namespace content negotiation
    location /twinship {
        # Serve Turtle to RDF clients
        if ($http_accept ~* "text/turtle") {
            return 303 https://ontology.twin-ship.eu/documentation/ontology.ttl;
        }

        # Serve RDF/XML to RDF clients
        if ($http_accept ~* "application/rdf\+xml") {
            return 303 https://ontology.twin-ship.eu/documentation/ontology.owl;
        }

        # Serve JSON-LD to JSON-LD clients
        if ($http_accept ~* "application/ld\+json") {
            return 303 https://ontology.twin-ship.eu/documentation/ontology.jsonld;
        }

        # Serve N-Triples to N-Triples clients
        if ($http_accept ~* "application/n-triples") {
            return 303 https://ontology.twin-ship.eu/documentation/ontology.nt;
        }

        # Default: redirect browsers to human-readable documentation
        return 303 https://ontology.twin-ship.eu/documentation/index-en.html;
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
RewriteRule ^twinship(.*)$ https://ontology.twin-ship.eu/documentation/ontology.ttl [R=303,L]

# RDF/XML
RewriteCond %{HTTP_ACCEPT} application/rdf\+xml
RewriteRule ^twinship(.*)$ https://ontology.twin-ship.eu/documentation/ontology.owl [R=303,L]

# JSON-LD
RewriteCond %{HTTP_ACCEPT} application/ld\+json
RewriteRule ^twinship(.*)$ https://ontology.twin-ship.eu/documentation/ontology.jsonld [R=303,L]

# N-Triples
RewriteCond %{HTTP_ACCEPT} application/n-triples
RewriteRule ^twinship(.*)$ https://ontology.twin-ship.eu/documentation/ontology.nt [R=303,L]

# Default: HTML documentation
RewriteRule ^twinship(.*)$ https://ontology.twin-ship.eu/documentation/index-en.html [R=303,L]
```

## How Fragment Identifiers Work

Entity IRIs use a hash namespace: `https://twin-ship.eu/twinship#EngineSystem`. The
`#EngineSystem` part is a **fragment identifier** — the browser never sends it to the
server. Instead:

1. Browser requests `https://twin-ship.eu/twinship`
2. Server responds with `303 See Other` → `https://ontology.twin-ship.eu/documentation/index-en.html`
3. Browser follows redirect and appends the original fragment: `https://ontology.twin-ship.eu/documentation/index-en.html#https://twin-ship.eu/twinship#EngineSystem`
4. The WIDOCO documentation page uses these fragment identifiers as HTML anchors, so the browser scrolls to the correct class definition.

This is why hash namespaces are convenient — a single redirect rule handles all entities.

## Verifying the Setup

After configuring redirects, verify with `curl`:

```bash
# HTML redirect (browser behavior)
curl -sI -H "Accept: text/html" https://twin-ship.eu/twinship
# Expected: 303 with Location: https://ontology.twin-ship.eu/documentation/index-en.html

# Turtle redirect (RDF tool behavior)
curl -sI -H "Accept: text/turtle" https://twin-ship.eu/twinship
# Expected: 303 with Location: https://ontology.twin-ship.eu/documentation/ontology.ttl

# RDF/XML redirect
curl -sI -H "Accept: application/rdf+xml" https://twin-ship.eu/twinship
# Expected: 303 with Location: https://ontology.twin-ship.eu/documentation/ontology.owl
```

## Notes

- **Use 303 (See Other)**, not 301 or 302. The 303 status code is the correct HTTP
  response for ontology IRIs per Linked Data conventions — it indicates that the requested
  resource is described by the document at the redirect target.
- The `/twinship/base` and `/twinship/core` paths (ontology-level IRIs without the `#`)
  could also benefit from similar redirects if external tools attempt to dereference them.
- CORS headers may be needed on `ontology.twin-ship.eu` if RDF tools fetch ontology files
  via JavaScript (e.g., `Access-Control-Allow-Origin: *`).
