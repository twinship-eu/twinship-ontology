# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Changed
- Separated WIDOCO documentation and WebVOWL visualization into two distinct pipelines
- Improved WebVOWL visualization by filtering external ontologies and using virtual properties to eliminate blank union nodes
- Switched to WIDOCO's built-in OWL2VOWL converter for WebVOWL generation
- Fixed WIDOCO HTML not displaying `skos:notation`, `skos:altLabel`, and `dcterms:description` annotation properties
- Fixed WebVOWL interactive visualization not displaying `skos:notation`, `skos:altLabel`, and `dcterms:description` annotations

## [0.0.3] - 2026-02-25

### Changed
- Enhanced visualization script to extract property ranges from OWL restrictions, enabling proper display of `directlyConnectedTo`, `connectedTo`, and `partOf` relationships in WebVOWL
- Fixed WebVOWL blank union nodes for multi-domain properties
- Added inter-component relationships to vessel ontology
- Specify UTF-8 when generating WebVOWL index.html

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
