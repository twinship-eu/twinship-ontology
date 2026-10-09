#!/usr/bin/env python3
"""
Patch WebVOWL so entity IRI links in "Selection Details" open the WIDOCO
documentation instead of dereferencing https://twin-ship.eu/twinship#X (404 until
the server-side redirect exists; see docs/SERVER_DEPLOYMENT.md, option B).

Usage:
    uv run python scripts/patch_webvowl_links.py docs/website/documentation/webvowl/js/webvowl.app.js
"""

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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)
    sys.exit(0 if patch(path) else 1)
