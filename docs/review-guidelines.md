# Review guidelines

What a review of a pull request checks before it is approved. The guidelines are for everyone who reviews: a person, the reviewer agent ([`.claude/agents/pr-reviewer.md`](../.claude/agents/pr-reviewer.md)) or another agent. Authors can use them to check their own work first. The procedure is below and, in short, in [CONTRIBUTING.md](../CONTRIBUTING.md#review); the rules themselves are in [CLAUDE.md](../CLAUDE.md).

## Procedure

- **The reviewer agent:** a Claude Code session runs the reviewer agent on every branch before it opens the pull request, for example by asking Claude Code to "run the pr-reviewer agent on branch <name>". It reads the change and reports findings without changing anything; that is an instruction, not a technical restriction. It runs on Claude Fable (`model: fable`, an alias that follows the current version), usually a different model from the one that wrote the change; if the author used the same model, say so in the pull request.
- **The author fixes what holds up** before opening the pull request, and answers the rest.
- **The review is posted** as the first comment on the pull request, once it is opened. The comment starts with a status line: either all findings were handled before opening, or which are still open. Then comes the reviewer's report, unchanged, except that anything it quotes that may not be in the repository (see the confidentiality rules below) is replaced with a description, for example "a real project name". Under each finding, a line says how it was handled: fixed in which commit, answered, or left and why. A review without findings is posted too. The description gets one line: who reviewed, on which model, and that the report is in the comments. A later review, after larger changes, is posted as a new comment.
- **Posting is part of opening the pull request:** a Claude Code session asked to open one also posts the review (`gh pr comment <number> --body-file <file>`). Without access, it gives the author the text to paste.
- **Without Claude Code,** check your own pull request against these guidelines and ask the maintainer to run the reviewer agent and post its report before approving it.
- The review is advisory: CI (`lint-and-test`) is the required check, and the maintainer approves.

## How to review

- **Read the diff and the files around it,** not only the description. Check every claim against the change: a finding you haven't verified is a question, not a finding.
- **Report what is wrong or missing,** each finding with its file and line, what is wrong, why it matters (a concrete case where it goes wrong), and a fix where one is clear.
- **Rank the findings:**
  - **must fix:** a wrong model, a broken rule below, a missing piece the pull request needs;
  - **should fix:** a real problem, but not blocking;
  - **question:** something to clarify.
- **Leave out taste.** Wording and style only count where a rule below says so.
- **"No findings" is a valid result.** Don't pad the review.

## Already checked by CI

The `lint-and-test` workflow fails on these, so a review only needs to look at them when CI hasn't run or fails: no `rdfs:domain` in `model/`, version numbers in sync, every property with a class restriction (or allow-listed in `tests/test_repository_rules.py`), SHACL `sh:datatype` matching `rdfs:range`, the competency questions marked `# STRICT`, ruff, black and REUSE.

## What to check

### 1. Correctness

- The change does what the description says, and nothing it doesn't mention.
- The model says what is meant: a class is a kind of thing, not a role or a state; a property's range and the restriction on its owning class agree; `owl:qualifiedCardinality` only where exactly one value is required.
- Labels and comments describe the term correctly, including its unit and sign conventions (for example trim positive by the stern).
- Tests or competency questions cover the change where it matters; expected results change only on purpose, and the description says why.

### 2. What the pull request includes

- The checks for what changed were run, and are listed in the description (see [CONTRIBUTING.md](../CONTRIBUTING.md)).
- **CHANGELOG.md** has a line under `[Unreleased]` for every change a user of the ontology would notice.
- The documentation changes in the same pull request: `model/README.md` for new terms or modules, the other READMEs, and `CLAUDE.md` when commands, folders or rules change.
- A new module is in `model/catalog-v001.xml` and imported by `model/twinship-core.ttl`; module imports stay a DAG.
- A release pull request bumps every version location listed in `CLAUDE.md` (Common Pitfalls 10), dates the changelog section and regenerates `STATISTICS.md`.
- The pull request targets `develop` (or `main` for a release), from a short-lived branch.

### 3. Modelling rules

- **Restrictions, not domains:** every class declares `owl:someValuesFrom` restrictions for its characteristic object and data properties; every property has `rdfs:range` (XSD for data properties, a class for object properties).
- **QUDT pattern:** a new numeric data property has its quantity-kind family in `twinship-qudt-vocabulary.ttl` (or reuses one with the right unit) and a `hasQuantity…` restriction on the owning class. The `tw…` data property is kept alongside.
- **Naming:** classes PascalCase (`TwinShip…` for foundation classes, acronyms in capitals), object properties lowerCamelCase, data properties `tw` + UpperCamelCase + unit suffix (none for dimensionless values, counts, identifiers and dates); labels in sentence case.
- **Unknown values** are omitted; never `-1` or another sentinel, also not in examples or shapes.
- **Module boundaries:** each term is in the module `CLAUDE.md` gives it; vessel- or engine-specific individuals (engine modes, speed bins, draft and trim modes) are instance data, not part of the shared modules. No obsolete module is created or referenced.
- **VesselAI:** never imported, no `owl:equivalentClass` or `skos:closeMatch`; only `rdfs:seeAlso` or `skos:relatedMatch`.
- **SHACL shapes** (`shapes/`) cover new properties where their siblings have shapes, and stay outside the ontology's imports.

### 4. Standards traceability

- A data property that matches an IMO or ISO definition has `skos:notation`, `skos:altLabel`, `dcterms:description` and `dcterms:source` together, as in `model/README.md`.
- Text from the IMO Compendium is not copied beyond what its terms allow; the extracted compendium is never committed.

### 5. Generated files

- Nothing under `build/` or `docs/website/documentation/` is edited by hand or committed, except `build/.gitkeep`.
- Website changes are made in `scripts/generate_website.sh`, not in generated HTML.

### 6. Confidentiality

- No secrets: no keys, tokens, passwords or Keycloak client details, and no `.env` content beyond what is committed.
- No vessel data from the operators, and no instance identifiers or vessel names in committed tests or queries; `examples/` datasets stay ignored until published.
- No internal addresses (servers, GraphDB repositories of a deployment).
- Nothing refers to notes or documents outside the repository that readers can't open; `papers/` and `data/` stay ignored.

### 7. Licences

- Contributions come in under the repository's terms (`REUSE.toml`): ontology, examples, queries and documentation CC BY 4.0, code MIT. A new file type or folder is covered by `REUSE.toml`.
- Every TwinShip `owl:Ontology` header states `dcterms:license <https://creativecommons.org/licenses/by/4.0/>`.
- Third-party material only where its licence allows, with its attribution.

### 8. Writing

- Documentation is in English, plain and short, and describes the current state.
