#!/usr/bin/env python3
"""
Patch WebVOWL so entity IRI links in "Selection Details" open the WIDOCO
documentation instead of dereferencing https://twin-ship.eu/twinship#X (404 until
the server-side redirect exists; see docs/SERVER_DEPLOYMENT.md, option B).

The patched script is then renamed to webvowl.app.<hash>.js and referenced from
webvowl/index.html, because the host kept serving a stale pre-compressed copy of
the old webvowl.app.js after a deploy.

Usage:
    uv run python scripts/patch_webvowl_links.py docs/website/documentation/webvowl/js/webvowl.app.js
"""

import hashlib
import re
import sys
from pathlib import Path

NAMESPACE = "https://twin-ship.eu/twinship#"
MARKER = "twinshipDocLink"

HELPER = f"""function {MARKER}( iri ){{
            // WIDOCO anchors use the full IRI as element id; webvowl/ sits next to index-en.html.
            if ( iri && iri.indexOf("{NAMESPACE}") === 0 ) return "../index-en.html#" + iri;
            return iri;
          }}

          function appendIriLabel("""


def patch(js_path):
    js = js_path.read_text(encoding="utf-8")

    if MARKER in js:
        print(f"WebVOWL links already patched: {js_path}")
        return True

    href_pattern = re.compile(r'\.attr\("href",\s*iri\s*\)')
    if "function appendIriLabel(" not in js or not href_pattern.search(js):
        print(f"Error: appendIriLabel not found in {js_path}; WebVOWL version changed?", file=sys.stderr)
        return False

    js = js.replace("function appendIriLabel(", HELPER, 1)
    js = href_pattern.sub(f'.attr("href", {MARKER}(iri))', js, count=1)
    js_path.write_text(js, encoding="utf-8")
    print(f"Patched WebVOWL IRI links: {js_path}")
    return True


def fingerprint(js_path):
    """Rename js_path to webvowl.app.<hash>.js and point webvowl/index.html at it."""
    index_path = js_path.parent.parent / "index.html"
    html = index_path.read_text(encoding="utf-8")

    script_pattern = re.compile(r'js/webvowl\.app(?:\.[0-9a-f]{8})?\.js')
    if not script_pattern.search(html):
        print(f"Error: webvowl.app.js script tag not found in {index_path}", file=sys.stderr)
        return False

    digest = hashlib.sha256(js_path.read_bytes()).hexdigest()[:8]
    target = js_path.with_name(f"webvowl.app.{digest}.js")
    if target != js_path:
        target.write_bytes(js_path.read_bytes())
        js_path.unlink()
    index_path.write_text(script_pattern.sub(f"js/{target.name}", html), encoding="utf-8")
    print(f"WebVOWL script fingerprinted: {target.name}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)
    sys.exit(0 if patch(path) and fingerprint(path) else 1)
