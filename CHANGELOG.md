# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.0.2] - 2026-02-06

### Changed
- **Namespace standardization**: All ontology files now use `https://twin-ship.eu/twinship#` as the main namespace prefix, with individual file URIs under `https://twin-ship.eu/twinship/` (e.g., `/base`, `/core`, `/vessel`, `/weatherconditions`)
- **Module consolidation**: Merged `engine.ttl` and `hull.ttl` into a single `vessel.ttl` module for simplified structure
- Updated `twinship-base.ttl`, `twinship-core.ttl`, and all module files to use consistent namespace patterns
- Fixed syntax errors in `twinship-core.ttl` imports
- Improved property annotations to explicitly reference ISO and IMO standards.

## [0.0.1] - 2026-02-04

### Added
- Initial repository structure with modular ontology architecture
- TwinShip base ontology with OWL restriction-based modeling approach
- Engine module (propulsion, fuel types, gearbox systems)
- Hull module (vessel types and properties)
- Weather conditions module
- Documentation generation pipeline using WIDOCO and WebVOWL
- Automated build scripts for ontology merging and visualization conversion
