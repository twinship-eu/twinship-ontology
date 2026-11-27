# Contributing to TwinShip Ontology

Thank you for your interest in contributing to the TwinShip Ontology! We welcome contributions from the community to improve and extend the ontology.

## How to Contribute

1. **Fork the repository** and create your branch from `develop`.
2. **Make your changes** in a modular and well-documented manner.
3. **Validate your changes** using the scripts in `scripts/` and tests in `tests/`.
4. **Submit a pull request** into `develop` with a clear description of your changes and the motivation behind them.

`develop` is the default branch. `main` holds released versions only and is updated through release pull requests from `develop`.

Pull requests must pass the CI check `lint-and-test` (ruff, black, REUSE lint, module merge, pytest). Run it locally with `uv run ruff check scripts tests`, `uv run black --check scripts tests` and `uv run pytest tests/` (after merging the modules; see [tests/README.md](tests/README.md)).

## Guidelines

- Follow the modular structure for ontology files (base, core, modules, vocabularies, external).
- Use clear, descriptive commit messages.
- Add or update documentation in `docs/` as needed.
- Ensure all new or modified ontology files are valid RDF/Turtle.
- Add or update SHACL shapes in `shapes/` or SPARQL tests in `tests/` if relevant.
- Contributions to the ontology (`model/`) and other knowledge artefacts are made under CC BY 4.0; code contributions (`scripts/`, Python tests, shell scripts) are made under MIT. See `REUSE.toml`.

## Review

Every pull request is reviewed against [docs/review-guidelines.md](docs/review-guidelines.md) before it is approved, and the review is posted on the pull request: correctness, what the pull request includes, the modelling rules, traceability, confidentiality and licences.

- **Before opening:** your Claude Code session runs the reviewer agent ([`.claude/agents/pr-reviewer.md`](.claude/agents/pr-reviewer.md)) on the branch, for example by asking it to "run the pr-reviewer agent on branch <name>". It reads the change and reports findings without changing anything; that is an instruction, not a technical restriction. It runs on Claude Fable (`model: fable`, an alias that follows the current version), usually a different model from the one that wrote the change; if the author used the same model, say so in the pull request. The author fixes what holds up and answers the rest.
- **When opening:** the session posts the report as the pull request's first comment, starting with a status line (all findings handled, or which are open), with a line under each finding saying how it was handled; the description gets one line saying who reviewed, on which model, and that the report is in the comments. Details: [docs/review-guidelines.md](docs/review-guidelines.md#procedure).
- **Without Claude Code,** check your own pull request against the guidelines and ask a maintainer to run the reviewer agent and post its report before approving it.
- The review is advisory: CI (`lint-and-test`) is the required check, and the maintainer approves.

## Code of Conduct

Please be respectful and constructive in all interactions.

## Questions?

Open an issue or contact the maintainers for help.
