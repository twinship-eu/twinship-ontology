"""
align_imo.py — Two-step IMO Compendium alignment workflow.

Step 1 — Prepare:
    Analyses all TwinShip modules using rdflib, generates ranked IMO candidate
    matches for every unlinked data property, and writes/updates a committed
    review CSV.  Previously decided rows (confirm / reject / iso) are preserved
    across re-runs so review progress is never lost.

    uv run python scripts/align_imo.py --prepare

Step 2 — Apply:
    Reads confirmed rows from the review CSV and injects the four IMO annotation
    triples (skos:notation, skos:altLabel, dcterms:description, dcterms:source)
    directly into the source .ttl files.  Safe to re-run — already-annotated
    properties are skipped.

    uv run python scripts/align_imo.py --apply --dry-run   # preview only
    uv run python scripts/align_imo.py --apply             # write to files

Review CSV (working artifact, gitignored):
    data/imo_alignment_review.csv

Columns:
    module          — TTL file stem (e.g. "vessel", "weather-conditions")
    tw_property     — local name with prefix (e.g. ":twFuelConsumptionTotalInMT")
    tw_label        — rdfs:label value
    imo_code        — candidate IMO code (e.g. "IMO0670")
    imo_name        — IMO element name
    imo_definition  — IMO element definition
    score           — matching score (higher = better candidate)
    action          — leave blank to review; set to:
                        confirm  →  inject this row's IMO code into the .ttl
                        reject   →  no IMO equivalent; skip this property
                        iso      →  aligned to ISO/other standard; skip

Prerequisites:
    model/external/imo/imo_compendium_all.csv must exist.
    Generate it with: uv run python scripts/extract_imo_compendium.py
"""

import argparse
import csv
import math
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = REPO_ROOT / "model"
MODULES_DIR = MODEL_DIR / "modules"
IMO_DIR = MODEL_DIR / "external" / "imo"
COMPENDIUM_CSV = IMO_DIR / "imo_compendium_all.csv"
REVIEW_CSV = REPO_ROOT / "data" / "imo_alignment_review.csv"

IMO_SOURCE_URI = "<https://www.imo.org/>"

# Modules to analyse, in display order
MODULE_FILES = [
    MODULES_DIR / "vessel.ttl",
    MODULES_DIR / "weather-conditions.ttl",
    MODULES_DIR / "operational-context.ttl",
    MODULES_DIR / "operational-modes.ttl",
]

REVIEW_FIELDNAMES = [
    "module",
    "tw_property",
    "tw_label",
    "imo_code",
    "imo_name",
    "imo_definition",
    "score",
    "action",
]

# Number of ranked candidates to generate per unlinked property
TOP_N_CANDIDATES = 5

# Namespace prefix for TwinShip entities
TS_PREFIX = "https://twin-ship.eu/twinship#"

# Actions that indicate the reviewer has made a decision
DECIDED_ACTIONS = {"confirm", "reject", "iso"}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def load_compendium() -> list[dict]:
    """Load imo_compendium_all.csv.  Fails clearly if not present."""
    if not COMPENDIUM_CSV.exists():
        print(
            f"ERROR: {COMPENDIUM_CSV.relative_to(REPO_ROOT)} not found.\n"
            "Generate it first with:\n"
            "    uv run python scripts/extract_imo_compendium.py",
            file=sys.stderr,
        )
        sys.exit(1)

    rows: list[dict] = []
    with open(COMPENDIUM_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    print(f"✓  Loaded {len(rows)} IMO elements from {COMPENDIUM_CSV.relative_to(REPO_ROOT)}")
    return rows


def tokenize(s: str) -> set[str]:
    """Lowercase word tokens, excluding common stopwords."""
    stopwords = {
        "the", "of", "in", "a", "an", "and", "or", "is", "at", "to",
        "by", "for", "be", "as", "its", "that", "this", "with", "since",
        "last", "reporting", "measure", "measured", "value",
    }
    tokens = set(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())
    return tokens - stopwords


def score_candidates(
    label: str, elements: list[dict]
) -> list[tuple[float, dict]]:
    """Return (score, element) pairs sorted descending for a property label."""
    query_tokens = tokenize(label)
    if not query_tokens:
        return []

    scored: list[tuple[float, dict]] = []
    for el in elements:
        el_tokens = tokenize(f"{el['name']} {el['definition']}")
        overlap = len(query_tokens & el_tokens)
        if overlap == 0:
            continue
        name_tokens = tokenize(el["name"])
        name_overlap = len(query_tokens & name_tokens)
        score = round(
            overlap / math.sqrt(len(query_tokens) * max(len(el_tokens), 1))
            + 0.5 * name_overlap,
            3,
        )
        scored.append((score, el))

    return sorted(scored, key=lambda x: x[0], reverse=True)


# ---------------------------------------------------------------------------
# --prepare: module analysis using rdflib
# ---------------------------------------------------------------------------


def analyse_module(ttl_path: Path) -> tuple[list[dict], list[dict]]:
    """
    Parse a module TTL with rdflib and return (linked, unlinked) property lists.

    Each item: {"local_name": ":twFoo", "label": "..."}
    linked   — properties that already have a skos:notation annotation
    unlinked — properties without skos:notation
    """
    try:
        from rdflib import Graph, RDF, OWL, RDFS
        from rdflib.namespace import SKOS
    except ImportError:
        print("ERROR: rdflib is required. Run: uv sync", file=sys.stderr)
        sys.exit(1)

    g = Graph()
    g.parse(str(ttl_path), format="turtle")

    linked: list[dict] = []
    unlinked: list[dict] = []

    for prop in g.subjects(RDF.type, OWL.DatatypeProperty):
        prop_str = str(prop)
        # Only consider TwinShip-namespaced properties
        if not prop_str.startswith(TS_PREFIX):
            continue
        local = prop_str[len(TS_PREFIX):]
        local_name = f":{local}"

        label_obj = g.value(prop, RDFS.label)
        label = str(label_obj) if label_obj else local

        notation = g.value(prop, SKOS.notation)
        if notation:
            linked.append({"local_name": local_name, "label": label})
        else:
            unlinked.append({"local_name": local_name, "label": label})

    # Sort for deterministic output
    linked.sort(key=lambda x: x["local_name"])
    unlinked.sort(key=lambda x: x["local_name"])
    return linked, unlinked


def load_existing_review() -> dict[tuple[str, str], list[dict]]:
    """
    Load all rows from the current review CSV grouped by (module, tw_property).
    Returns {} if the file does not exist yet.
    """
    if not REVIEW_CSV.exists():
        return {}

    existing: dict[tuple[str, str], list[dict]] = {}
    with open(REVIEW_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["module"], row["tw_property"])
            existing.setdefault(key, []).append(row)
    return existing


def cmd_prepare(args) -> None:
    """--prepare: analyse all modules, write/update the review CSV."""
    elements = load_compendium()
    existing = load_existing_review()

    module_stats: list[dict] = []
    output_rows: list[dict] = []  # final rows for review CSV

    for ttl_path in MODULE_FILES:
        if not ttl_path.exists():
            print(f"  ⚠  Skipping {ttl_path.name} (file not found)")
            continue

        module = ttl_path.stem
        print(f"\n📦 Analysing {ttl_path.relative_to(REPO_ROOT)} ...")

        linked, unlinked = analyse_module(ttl_path)
        print(f"   {len(linked)} already annotated  |  {len(unlinked)} unlinked")

        preserved_count = 0
        with_candidates = 0
        without_candidates = 0

        for item in unlinked:
            key = (module, item["local_name"])

            # Preserve all rows for properties that already have a decision
            if key in existing:
                prop_rows = existing[key]
                has_decision = any(
                    r.get("action", "").strip().lower() in DECIDED_ACTIONS
                    for r in prop_rows
                )
                if has_decision:
                    output_rows.extend(prop_rows)
                    preserved_count += 1
                    continue
                # No decision yet — fall through to regenerate candidates

            candidates = score_candidates(item["label"], elements)[:TOP_N_CANDIDATES]

            if candidates:
                for score, el in candidates:
                    output_rows.append({
                        "module":          module,
                        "tw_property":     item["local_name"],
                        "tw_label":        item["label"],
                        "imo_code":        el["imo_code"],
                        "imo_name":        el["name"],
                        "imo_definition":  el["definition"],
                        "score":           score,
                        "action":          "",
                    })
                with_candidates += 1
            else:
                # No plausible IMO match found
                output_rows.append({
                    "module":          module,
                    "tw_property":     item["local_name"],
                    "tw_label":        item["label"],
                    "imo_code":        "",
                    "imo_name":        "",
                    "imo_definition":  "",
                    "score":           "",
                    "action":          "",
                })
                without_candidates += 1

        module_stats.append({
            "module":             module,
            "total":              len(linked) + len(unlinked),
            "annotated":          len(linked),
            "unlinked":           len(unlinked),
            "preserved":          preserved_count,
            "with_candidates":    with_candidates,
            "without_candidates": without_candidates,
        })

    # Write the review CSV
    REVIEW_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)

    # Print summary table
    print()
    col_w = 28
    hdr = (
        f"  {'Module':<{col_w}} {'Total':>6} {'Annotated':>9} "
        f"{'Unlinked':>8} {'Preserved':>9} {'Candidates':>10} {'No match':>8}"
    )
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for s in module_stats:
        print(
            f"  {s['module']:<{col_w}} {s['total']:>6} {s['annotated']:>9} "
            f"{s['unlinked']:>8} {s['preserved']:>9} "
            f"{s['with_candidates']:>10} {s['without_candidates']:>8}"
        )

    review_rel = REVIEW_CSV.relative_to(REPO_ROOT)
    total_new = sum(
        s["with_candidates"] + s["without_candidates"] for s in module_stats
    )
    total_preserved = sum(s["preserved"] for s in module_stats)
    print(f"\n✓  Review CSV written → {review_rel}")
    print(
        f"   {len(output_rows)} total rows  "
        f"({total_new} new properties, {total_preserved} preserved decisions)"
    )
    print(
        "\n📋 Next steps:"
        f"\n   1. Open {review_rel} in a spreadsheet"
        f"\n   2. Each unlinked property shows up to {TOP_N_CANDIDATES} ranked candidates"
        "\n      Set action=confirm on the best matching row"
        "\n      Set action=reject if none are correct (no IMO equivalent)"
        "\n      Set action=iso if the property maps to a non-IMO standard"
        "\n   3. Preview:  uv run python scripts/align_imo.py --apply --dry-run"
        "\n      Apply:    uv run python scripts/align_imo.py --apply"
    )


# ---------------------------------------------------------------------------
# --apply: inject confirmed annotations back into .ttl files
# ---------------------------------------------------------------------------


def inject_annotations(
    ttl_text: str,
    local_name: str,
    imo_code: str,
    imo_name: str,
    imo_definition: str,
) -> tuple[str, bool]:
    """
    Insert the four IMO annotation triples into ttl_text after rdfs:comment
    for the property identified by local_name (e.g. ":twFuelConsumptionTotalInMT").

    Returns (modified_text, did_inject).
    Returns (ttl_text, False) if the property is not found, already annotated,
    or has no rdfs:comment to anchor to.
    """
    # Find the property declaration — anchored to start of line
    prop_re = re.compile(
        r"^" + re.escape(local_name) + r"[ \t]+a[ \t]+owl:DatatypeProperty",
        re.MULTILINE,
    )
    prop_match = prop_re.search(ttl_text)
    if not prop_match:
        return ttl_text, False

    # Inspect a window large enough to contain any property block (2000 chars)
    window_start = prop_match.start()
    window = ttl_text[window_start: window_start + 2000]

    # Skip if already annotated with any notation
    if "skos:notation" in window:
        return ttl_text, False

    # Find rdfs:comment line — always single-line in this codebase
    comment_re = re.compile(r'    rdfs:comment "(?:[^"\\]|\\.)*"[ \t]*;[ \t]*\n')
    cm = comment_re.search(window)
    if not cm:
        return ttl_text, False

    # Escape any double-quotes in the IMO strings
    safe_def = imo_definition.replace("\\", "\\\\").replace('"', '\\"')
    safe_name = imo_name.replace("\\", "\\\\").replace('"', '\\"')

    injection = (
        f'    skos:notation "{imo_code}" ;\n'
        f'    skos:altLabel "{safe_name}" ;\n'
        f'    dcterms:description "{safe_def}" ;\n'
        f'    dcterms:source {IMO_SOURCE_URI} ;\n'
    )

    # Absolute insert position in the full text
    abs_insert = window_start + cm.end()
    return ttl_text[:abs_insert] + injection + ttl_text[abs_insert:], True


def cmd_apply(args) -> None:
    """--apply: write confirmed rows from the review CSV into .ttl files."""
    if not REVIEW_CSV.exists():
        print(
            f"ERROR: {REVIEW_CSV.relative_to(REPO_ROOT)} not found.\n"
            "Run --prepare first to generate the review CSV.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load confirmed rows
    confirmed: list[dict] = []
    with open(REVIEW_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("action", "").strip().lower() == "confirm":
                confirmed.append(row)

    if not confirmed:
        print("No rows with action=confirm found in the review CSV.  Nothing to apply.")
        return

    print(f"✓  Found {len(confirmed)} confirmed rows")

    # Group by module
    by_module: dict[str, list[dict]] = {}
    for row in confirmed:
        by_module.setdefault(row["module"], []).append(row)

    module_path_map = {ttl.stem: ttl for ttl in MODULE_FILES}

    total_applied = 0
    total_skipped = 0

    for module, rows in sorted(by_module.items()):
        ttl_path = module_path_map.get(module)
        if ttl_path is None or not ttl_path.exists():
            print(f"  ⚠  Module '{module}' not found — skipping {len(rows)} rows")
            continue

        ttl_text = ttl_path.read_text(encoding="utf-8")
        applied = 0
        skipped = 0

        # De-duplicate: a reviewer might accidentally confirm multiple rows for the
        # same property.  Take the row with the highest score.
        seen: set[str] = set()
        deduped: list[dict] = []
        for row in sorted(
            rows,
            key=lambda r: float(r["score"]) if r.get("score") else 0.0,
            reverse=True,
        ):
            if row["tw_property"] not in seen:
                seen.add(row["tw_property"])
                deduped.append(row)

        print(f"\n📦 {ttl_path.relative_to(REPO_ROOT)}  ({len(deduped)} properties)")

        for row in sorted(deduped, key=lambda r: r["tw_property"]):
            local_name = row["tw_property"]
            ttl_text, did_inject = inject_annotations(
                ttl_text,
                local_name,
                row["imo_code"],
                row["imo_name"],
                row["imo_definition"],
            )
            dry = "  (dry-run)" if args.dry_run else ""
            if did_inject:
                print(f"  ✓  {local_name}  →  {row['imo_code']}{dry}")
                applied += 1
            else:
                print(f"  ↩  {local_name}  — already annotated or not found, skipped")
                skipped += 1

        if applied > 0 and not args.dry_run:
            ttl_path.write_text(ttl_text, encoding="utf-8")
            print(f"  💾 Saved {ttl_path.relative_to(REPO_ROOT)}")

        total_applied += applied
        total_skipped += skipped

    if args.dry_run:
        print(
            f"\n🔍 Dry-run complete: {total_applied} annotations would be written, "
            f"{total_skipped} skipped"
        )
        print("   Re-run without --dry-run to apply changes.")
    else:
        print(
            f"\n✓  Done: {total_applied} properties annotated, {total_skipped} skipped"
        )
        if total_applied > 0:
            print(
                "   Re-run --prepare to refresh the review CSV and check remaining gaps."
            )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Two-step IMO Compendium alignment workflow for TwinShip ontology.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Workflow:\n"
            "  Step 1 — Generate candidates and review CSV:\n"
            "    uv run python scripts/align_imo.py --prepare\n"
            "\n"
            "  Step 2 — Apply confirmed alignments to .ttl files:\n"
            "    uv run python scripts/align_imo.py --apply --dry-run   # preview\n"
            "    uv run python scripts/align_imo.py --apply             # write\n"
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--prepare",
        action="store_true",
        help=(
            "Analyse all modules and generate/update "
            f"{REVIEW_CSV.relative_to(REPO_ROOT)}."
        ),
    )
    group.add_argument(
        "--apply",
        action="store_true",
        help="Write confirmed IMO annotations from the review CSV into .ttl files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --apply: show what would be written without modifying any file.",
    )
    args = parser.parse_args()

    if args.prepare:
        cmd_prepare(args)
    elif args.apply:
        cmd_apply(args)


if __name__ == "__main__":
    main()
