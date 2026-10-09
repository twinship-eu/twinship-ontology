# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- `operational-modes.ttl` module: categorical operating states and modes (`OperatingState`, `EngineMode`, `DraftMode`, `TrimMode`, `DraftTrimMode`) with named individuals (`CruiseState`, `PortState`, `ManeuveringState`, `DriftState`, etc.)
- `operational-context.ttl` module: voyage, port, and operational profile concepts (`Voyage`, `VoyageLeg`, `Route`, `Port`, `OperationalProfile`, `VesselSpeedBin`, `FrequencyDistribution`, `FuelConsumptionObservation`, `FuelConsumptionSummary`, `FuelConsumptionEstimate`, `FuelConsumptionGapAnalysis`, `PerformanceDeviation`)
- Naming conventions documented in `CLAUDE.md` and `model/README.md` (data property `tw` prefix, `"twinship <name>"` label pattern, unit suffix conventions)
- VesselAI full reuse audit (`docs/ontology/vesselai-full-reuse-audit.txt`)
- MIT license
- Ontology statistics
- `statistics.ttl` module (estimation, prediction, statistical models, and Model Card documentation aligned to MCRO) with competency question tests `CQE-01`–`CQE-31` (incl. `cqe28_prediction_engine_mode.rq`)

### Changed
- `statistics.ttl`: renamed Model Card data properties to the `tw` convention (`hasAlgorithm` → `twAlgorithm`, `hasConfidenceIntervalValue` → `twConfidenceIntervalValue`, `hasMetricValue` → `twMetricValue`, `hasEvaluationSlice` → `twEvaluationSlice`, `hasDocumentationSummary` → `twDocumentationSummary`); datatype ranges changed from `rdfs:Literal` to `xsd:string`; `documentsModel` range and restriction now use `owl:unionOf` / `owl:someValuesFrom`
- Added `EngineMode` kW range properties (`twEngineModeLowerBoundInKW`, `twEngineModeLowerBoundVariationInKW`, `twEngineModeUpperBoundInKW`) and `twEngineModeCount` on `EngineSystem`; `EngineMode` individuals are instantiated per engine in instance data, and an engine's roster is declared via `hasEngineMode`
- Renamed observed draft/loading properties in `vessel.ttl` to the `tw` + unit-suffix convention (`displacementTonnes` → `twDisplacementInMT`, `bowDraftValue` → `twBowDraftInM`, `sternDraftValue` → `twSternDraftInM`, `aftDraftValue` → `twAftDraftInM`, `foreDraftValue` → `twForeDraftInM`, `trimValue` → `twTrimInM`)
- Added optional `twEngineModeLowerBoundInRevPerMin` / `twEngineModeUpperBoundInRevPerMin` to `EngineMode` (engine RPM bounds for modes the statistical model bins on engine speed); model-internal mean/deviation are not stored on the mode. `EngineMode` comment now notes that a model re-fit should mint new individuals. Also added QUDT `hasQuantityPower` / `hasQuantityRotationalVelocity` restrictions on `EngineMode` (covering both the kW and RPM bounds).
- Tightened `VesselSpeedBin`'s `hasSpeedReference` restriction from `someValuesFrom` to `owl:onClass :SpeedReference ; owl:qualifiedCardinality "1"` (exactly one of SOG/STW required), now that both reference frames are populated side by side in real data; same pattern as `DraftTrimMode`'s `hasDraftMode`/`hasTrimMode` restrictions.
- Removed the `EngineSpeedBin1`-`4`, `DraftMode1`-`3`, `TrimMode1`-`3` named individuals (and their `owl:AllDifferent` blocks) from `operational-modes.ttl` — their meaning is vessel-/engine-specific, not shared across vessel types, same reasoning already applied to `EngineMode`. Futuristic vessel demonstrator placeholders now live in `twinship-futuristic-vessel/data/futuristic-vessel-individuals.ttl`, pending merge into `examples/futuristic-vessel.ttl`.
- Removed VesselAI import from `twinship-base.ttl` (DUL/DOLCE upper ontology incompatible with IDO; VesselAI files retained under `model/external/vesselai/` for reference only)
- Renamed all data properties in `weather-conditions.ttl` and `operational-context.ttl` to `tw` prefix convention (28 properties; e.g. `:windSpeed` → `:twWindSpeed`, `:voyageIdentifier` → `:twVoyageIdentifier`)
- Updated `rdfs:label` annotations to `"twinship <name>"` pattern throughout extension modules
- Added OWL `owl:someValuesFrom` restrictions to all classes in `weather-conditions.ttl` and `operational-context.ttl`, aligning with the design pattern established in `vessel.ttl`
- Added missing subject-side OWL restrictions for `hasEngineMode`, `hasDraftMode`, `hasTrimMode`, `hasDraftTrimMode`, `hasWeatherCondition` on `Voyage`/`VoyageLeg`
- Added `owl:imports <weather-conditions>` to `operational-context.ttl` (required for `hasWeatherCondition some WeatherCondition` restriction on `VoyageLeg`)
- `DraftTrimMode` is now a composed class (`hasDraftMode` + `hasTrimMode`, qualified cardinality 1 each) with no fixed enumerated individuals, following the same instantiation pattern as `VesselSpeedBin`
- Renamed `SpeedBin` to `VesselSpeedBin`; revised description to note SOG/STW divergence under weather/current influence
- Added `SpeedReference` class (`SOG`, `STW` individuals) and `hasSpeedReference` object property to `operational-modes.ttl`; applied as a qualifier restriction on `VesselSpeedBin` (made required, exactly one, see above)
- Added `twFuelCostInUsdPerMT` datatype property and restriction to `Fuel` (`vessel.ttl`)
- Documented a limitation on `EngineSpeedBin`: assumes mechanically-coupled propulsion
  (direct-drive/geared); may not apply to diesel-electric/hybrid vessels (e.g. the futuristic
  vessel), where engine (genset) speed is decoupled from propeller speed by the electrical
  system. Modeling this case is deferred pending domain expert input.
- Added `EngineSpeedBin` class and `hasEngineSpeedBin` object property to `operational-modes.ttl`, representing ordinal engine speed (RPM) regions from the engine-propeller combinator diagram; no individuals defined in the shared module, numeric RPM ranges deferred pending combinator diagram data
- Replaced ambiguous `twVoyageStartTime`/`twVoyageEndTime` with `twVoyageEstimatedStartTime`/`twVoyageActualStartTime` and `twVoyageEstimatedEndTime`/`twVoyageActualEndTime` (Estimated/Actual pattern, per DynaPort D2.3 ETD/ATD, ETA/ATA terminology)
- Added `twWayPointTimestamp` datatype property and restriction to `WayPoint`
- Added `twinship-core` as a node in the `modules.drawio` diagram (single entry point for the
  complete ontology, with import edges to `twinship-base` and all 5 domain modules); documented
  the "core stays minimal" principle in `model/README.md` — consumers needing a different subset
  should write their own small aggregate file rather than requesting an official package tier
- Explored then reverted having `vessel.ttl` import `operational-context.ttl` to add missing
  `VesselSystem` restrictions (`hasVoyage`, `hasOperatingState`, etc.). Reverted to keep `vessel.ttl`
  a lightweight `twinship-base`-only leaf module for modular/partial-ontology use; the gap (no
  formal restriction linking `VesselSystem` to `Voyage`/`OperatingState`/etc.) is reinstated as a
  known limitation
- Expanded `model/README.md` with corrected architecture diagram (import DAG), naming conventions reference, and design pattern documentation
- Updated `queries/weather-conditions-validation.rq` to reflect renamed properties

## [0.0.4] - 2026-03-03

### Changed
- Updated all version numbers to 0.0.4 across ontology files, project metadata, and documentation
- Fixed missing subPropertyOf for boiler DO return properties
- Filtered TwinShipInanimatePhysicalObject and partOf from WebVOWL visualization
- Added diesel-electric propulsion and green energy systems
- Added server deployment guide with redirect configuration
- Improved WebVOWL visualization and documentation pipelines
- Removed associatedEntity as it was not used in any restrictions, instances, or scripts

## [0.0.3] - 2026-02-25

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
