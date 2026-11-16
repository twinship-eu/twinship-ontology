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

## Code of Conduct

Please be respectful and constructive in all interactions.

## Questions?

Open an issue or contact the maintainers for help.
