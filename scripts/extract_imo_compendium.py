"""
extract_imo_compendium.py — Download and extract IMO Compendium data elements.

Downloads the IMO Compendium Excel (FAL.5/Circ.56) and exports all data
elements (BBIE rows) as a CSV for ontology review and alignment.

Usage:
    uv run python scripts/extract_imo_compendium.py
    uv run python scripts/extract_imo_compendium.py --keywords fuel temperature speed power pressure
    uv run python scripts/extract_imo_compendium.py --existing /path/to/IMO_Compendium.xlsx
    uv run python scripts/extract_imo_compendium.py --compare model/modules/vessel.ttl

Output files:
    model/external/imo/imo_compendium_all.csv  — all BBIE data elements (committed, stable reference)
    data/IMO_Compendium.xlsx                   — cached Excel download (gitignored, re-downloadable)
    data/imo_compendium_filtered.csv           — filtered by --keywords (gitignored, transient)
    data/imo_alignment_gaps.csv                — properties missing IMO codes (gitignored, transient)
"""

import argparse
import csv
import re
import sys
import urllib.request
from pathlib import Path

IMO_EXCEL_URL = (
    "https://imocompendium.imo.org/public/IMO-Compendium/Current/IMO%20Compendium.xlsx"
)

# Columns in the "IMO Data Set" sheet (0-based)
COL_PATH       = 0
COL_LEVEL      = 1
COL_KIND       = 2   # "BBIE" = Basic Business Information Entity (a data element)
COL_DATA_NUM   = 4   # "IMO0001", "IMO0628", etc.
COL_NAME       = 5   # Human-readable name
COL_DEFINITION = 6   # Definition text
COL_FORMAT     = 40  # Format (e.g., "an..35", "n..10")

SHEET_NAME = "IMO Data Set"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def download_excel(dest: Path) -> None:
    print(f"⬇  Downloading IMO Compendium from {IMO_EXCEL_URL} ...")
    urllib.request.urlretrieve(IMO_EXCEL_URL, dest)
    print(f"✓  Saved to {dest} ({dest.stat().st_size // 1024} KB)")


def load_elements(xlsx_path: Path) -> list[dict]:
    try:
        import openpyxl
    except ImportError:
        print("ERROR: openpyxl is required. Run: uv add openpyxl", file=sys.stderr)
        sys.exit(1)

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    if SHEET_NAME not in wb.sheetnames:
        print(f"ERROR: sheet '{SHEET_NAME}' not found. Available: {wb.sheetnames}",
              file=sys.stderr)
        sys.exit(1)

    ws = wb[SHEET_NAME]
    elements = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        kind      = row[COL_KIND]
        data_num  = row[COL_DATA_NUM]
        name      = row[COL_NAME]
        defn      = row[COL_DEFINITION]
        fmt       = row[COL_FORMAT] if len(row) > COL_FORMAT else None

        # Only keep BBIE rows that have an IMO data number
        if kind != "BBIE" or not data_num:
            continue

        elements.append({
            "imo_code":   str(data_num).strip(),
            "name":       str(name).strip()      if name else "",
            "definition": str(defn).strip()      if defn else "",
            "format":     str(fmt).strip()        if fmt  else "",
        })

    print(f"✓  Extracted {len(elements)} data elements from '{SHEET_NAME}'")
    return elements


def filter_by_keywords(elements: list[dict], keywords: list[str]) -> list[dict]:
    kw_lower = [k.lower() for k in keywords]
    results = []
    for el in elements:
        text = f"{el['name']} {el['definition']}".lower()
        if any(k in text for k in kw_lower):
            results.append(el)
    return results


def write_csv(rows: list[dict], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["imo_code", "name", "definition", "format"],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓  Written {len(rows)} rows → {dest}")


# ---------------------------------------------------------------------------
# alignment gap analysis
# ---------------------------------------------------------------------------

def extract_imo_codes_from_ttl(ttl_path: Path) -> dict[str, str]:
    """Return {imo_code: property_iri} for all skos:notation IMO codes in a .ttl file."""
    pattern = re.compile(
        r'(:\w+)\s+a\s+owl:DatatypeProperty.*?skos:notation\s+"(IMO\d+)"',
        re.DOTALL,
    )
    text = ttl_path.read_text(encoding="utf-8")
    return {m.group(2): m.group(1) for m in pattern.finditer(text)}


def find_unlinked_properties(ttl_path: Path) -> list[str]:
    """Return property IRIs that have no skos:notation IMO code annotation."""
    text = ttl_path.read_text(encoding="utf-8")
    # find all DatatypeProperty declarations
    all_props = re.findall(r'(:\w+)\s+a\s+owl:DatatypeProperty', text)
    # find those that already have an IMO notation
    linked = re.findall(
        r'(:\w+)\s+a\s+owl:DatatypeProperty.*?skos:notation\s+"IMO\d+"',
        text,
        re.DOTALL,
    )
    unlinked = [p for p in all_props if p not in linked]
    return unlinked


def match_ttl_to_imo(ttl_path: Path, elements: list[dict], out_path: Path) -> None:
    """For each unlinked property, score against IMO CSV by word overlap and write candidates."""
    import math

    unlinked = find_unlinked_properties(ttl_path)
    text = ttl_path.read_text(encoding="utf-8")

    # Build {prop: label} from rdfs:label
    label_map: dict[str, str] = {}
    for m in re.finditer(r'(:\w+)\s+a\s+owl:DatatypeProperty.*?rdfs:label\s+"([^"]+)"',
                         text, re.DOTALL):
        label_map[m.group(1)] = m.group(2)

    def tokenize(s: str) -> set[str]:
        return set(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())

    rows = []
    for prop in unlinked:
        label = label_map.get(prop, prop.lstrip(":"))
        query_tokens = tokenize(label)
        if not query_tokens:
            continue
        scored = []
        for el in elements:
            el_tokens = tokenize(f"{el['name']} {el['definition']}")
            overlap = len(query_tokens & el_tokens)
            if overlap == 0:
                continue
            # Jaccard-like score weighted toward name hits
            name_tokens = tokenize(el["name"])
            name_overlap = len(query_tokens & name_tokens)
            score = round(overlap / math.sqrt(len(query_tokens) * len(el_tokens))
                          + 0.5 * name_overlap, 3)
            scored.append((score, el))
        # Keep top 3 candidates per property
        for score, el in sorted(scored, key=lambda x: x[0], reverse=True)[:3]:
            rows.append({
                "tw_property":    prop,
                "tw_label":       label,
                "imo_code":       el["imo_code"],
                "imo_name":       el["name"],
                "imo_definition": el["definition"],
                "score":          score,
                "action":         "",  # fill in: confirm / reject
            })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["tw_property", "tw_label", "imo_code",
                        "imo_name", "imo_definition", "score", "action"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓  Candidate matches ({len(unlinked)} properties → {len(rows)} candidates) → {out_path}")
    print("    Review: set action='confirm' for correct matches, then apply with:")
    print("        uv run python scripts/align_imo.py --apply --dry-run")


def alignment_gap_report(ttl_path: Path, elements: list[dict], out_path: Path) -> None:
    unlinked = find_unlinked_properties(ttl_path)
    print(f"  {len(unlinked)} data properties have no IMO code annotation")

    # Read property labels to help manual matching
    text = ttl_path.read_text(encoding="utf-8")
    label_map: dict[str, str] = {}
    for m in re.finditer(r'(:\w+)\s+a\s+owl:DatatypeProperty.*?rdfs:label\s+"([^"]+)"',
                         text, re.DOTALL):
        label_map[m.group(1)] = m.group(2)

    rows = []
    for prop in unlinked:
        label = label_map.get(prop, "")
        rows.append({
            "tw_property":  prop,
            "tw_label":     label,
            "imo_code":     "",
            "imo_name":     "",
            "imo_definition": "",
            "note": "review needed",
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["tw_property", "tw_label", "imo_code",
                        "imo_name", "imo_definition", "note"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓  Gap report ({len(rows)} unlinked properties) → {out_path}")
    print("    Open the CSV, search the imo_compendium_all.csv for matching terms,")
    print("    then fill in imo_code / imo_name / imo_definition for each property.")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract IMO Compendium data elements for ontology alignment."
    )
    parser.add_argument(
        "--existing",
        metavar="PATH",
        help="Use an already-downloaded IMO Compendium .xlsx instead of downloading.",
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        metavar="WORD",
        default=[],
        help="Filter output to elements whose name or definition contains any keyword.",
    )
    parser.add_argument(
        "--match-ttl",
        metavar="TTL",
        help="Path to a .ttl file; generate ranked IMO candidate matches for unlinked properties.",
    )
    parser.add_argument(
        "--compare",
        metavar="TTL",
        help="Path to a .ttl file; generate a gap report of properties missing IMO codes.",
    )
    parser.add_argument(
        "--out-dir",
        metavar="DIR",
        default="model/external/imo",
        help="Output directory for compendium CSV and cached xlsx (default: model/external/imo/).",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)

    # 1. Obtain the Excel file
    if args.existing:
        xlsx_path = Path(args.existing)
        if not xlsx_path.exists():
            print(f"ERROR: file not found: {xlsx_path}", file=sys.stderr)
            sys.exit(1)
        print(f"📂 Using existing file: {xlsx_path}")
    else:
        # Excel is cached in data/ (gitignored transient artifact)
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        xlsx_path = data_dir / "IMO_Compendium.xlsx"
        if xlsx_path.exists():
            print(f"📂 Using cached file: {xlsx_path} (delete to re-download)")
        else:
            download_excel(xlsx_path)

    # 2 & 3. Load elements — reuse existing CSV when it is already newer than the
    # Excel file (i.e. the cached xlsx has not changed since last extraction).
    csv_path = out_dir / "imo_compendium_all.csv"
    csv_is_fresh = (
        csv_path.exists()
        and csv_path.stat().st_mtime >= xlsx_path.stat().st_mtime
    )
    if csv_is_fresh:
        print(f"📂 {csv_path} is up to date — skipping extraction")
        with open(csv_path, encoding="utf-8") as _f:
            elements = list(csv.DictReader(_f))
        print(f"✓  Loaded {len(elements)} data elements from existing CSV")
    else:
        elements = load_elements(xlsx_path)
        write_csv(elements, csv_path)

    # 4. Write filtered CSV to data/ (transient working artifact, gitignored)
    if args.keywords:
        print(f"\n🔍 Filtering by keywords: {args.keywords}")
        filtered = filter_by_keywords(elements, args.keywords)
        print(f"   {len(filtered)} matches")
        write_csv(filtered, Path("data") / "imo_compendium_filtered.csv")

    # 6. Match candidates against a .ttl file — written to data/ (transient)
    if args.match_ttl:
        ttl_path = Path(args.match_ttl)
        if not ttl_path.exists():
            print(f"ERROR: TTL file not found: {ttl_path}", file=sys.stderr)
            sys.exit(1)
        print(f"\n🔬 Generating IMO candidate matches for {ttl_path}")
        match_ttl_to_imo(ttl_path, elements, Path("data") / "imo_candidates.csv")

    # 7. Gap analysis against a .ttl file — written to data/ (transient)
    if args.compare:
        compare_path = Path(args.compare)
        if not compare_path.exists():
            print(f"ERROR: TTL file not found: {compare_path}", file=sys.stderr)
            sys.exit(1)
        print(f"\n🔎 Alignment gap analysis against {compare_path}")
        alignment_gap_report(compare_path, elements, Path("data") / "imo_alignment_gaps.csv")

    print(
        "\n📋 Next steps:"
        "\n   1. Open model/external/imo/imo_compendium_all.csv in a spreadsheet"
        "\n   2. Search/filter by domain keywords (fuel, speed, power, temperature, etc.)"
        "\n   3. For systematic alignment across all modules use align_imo.py:"
        "\n      uv run python scripts/align_imo.py --prepare"
        "\n      (opens data/imo_alignment_review.csv for review, then --apply)"
        "\n   4. For manual one-off annotations, add to the .ttl file:"
        '\n      skos:notation "IMO####" ;'
        '\n      skos:altLabel "<IMO name>" ;'
        '\n      dcterms:description "<IMO definition>" ;'
        '\n      dcterms:source <https://www.imo.org/> ;'
    )


if __name__ == "__main__":
    main()
