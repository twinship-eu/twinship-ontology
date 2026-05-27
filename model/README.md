# TwinShip Ontology - Model Directory

This directory contains the TwinShip ontology organized in a **modular architecture** with a foundation layer and domain-specific modules.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     twinship-core.ttl (Complete)                                 │  ← Import this for
│                     Aggregate of base + all modules                              │    full ontology
└───┬──────────────────┬─────────────────────┬────────────────────────┬────────────┘
    │ imports          │ imports             │ imports                │ imports
    ▼                  ▼                     ▼                        ▼
┌──────────┐  ┌──────────────────┐  ┌────────────────────┐  ┌──────────────────────┐
│ twinship │  │ modules/         │  │ modules/           │  │ modules/             │
│  -base   │  │ vessel.ttl       │  │ weather-           │  │ operational-context  │
│          │  │                  │  │ conditions.ttl     │  │ .ttl                 │
│ Base     │  │ Vessels, Engines │  │ Weather, Wind      │  │ Voyages, Ports,      │
│ classes, │  │ Propulsion,      │  │ conditions         │  │ Profiles, Statistics │
│ props    │  │ Fuel, Gearbox    │  │                    │  └──┬──────────┬─────────┘
└────┬─────┘  └────────┬─────────┘  └────────┬───────────┘     │ imports  │ imports
     │                 │                     │◄────────────────┘          │
     │◄────────────────┘                     │                            ▼
     │                                       │               ┌──────────────────────┐
     │◄──────────────────────────────────────┘               │ modules/             │
     │◄──────────────────────────────────────────────────────┤ operational-modes    │
     │                                                       │ .ttl                 │
     ▼                                                       │ States, Modes,       │
┌──────────────────────────────────────────────────────┐     │ Draft/Trim modes     │
│  External Ontologies (imported): IDO, PAV, QUDT      │     └──────────────────────┘
└──────────────────────────────────────────────────────┘
```

**Import dependency summary:**
- `vessel`, `weather-conditions`, `operational-modes` each import only `twinship-base`
- `operational-context` imports `twinship-base` + `operational-modes` + `weather-conditions`
- No circular dependencies — the graph is a strict DAG

## Directory Structure

```
model/                          # Source ontology files (version controlled)
├── twinship-base.ttl           # Foundation ontology (base classes, properties)
├── twinship-core.ttl           # Complete aggregate (imports base + all modules)
├── modules/                    # Domain-specific modules
│   ├── vessel.ttl              # Vessels, engines, propulsion, fuel, gearbox
│   ├── weather-conditions.ttl  # Weather and wind condition classes
│   ├── operational-modes.ttl   # Categorical operating states, engine modes, draft/trim modes
│   └── operational-context.ttl # Voyages, ports, profiles, observations, summaries
├── external/                   # External ontology dependencies
│   ├── IDO_20240503.ttl        # ISO 15926-14 upper ontology
│   ├── PAV-simplified.ttl      # Provenance, Authoring and Versioning
│   ├── SCHEMA_QUDT-simplified.ttl
│   └── vesselai/               # External reference only, not imported
├── vocabularies/               # QUDT vocabularies
│   ├── VOCAB_QUDT-QUANTITY-KINDS-simplified.ttl
│   └── VOCAB_QUDT_UNIT2-simplified.ttl
└── catalog-v001.xml            # Protégé catalog for URI resolution

build/                          # Auto-generated build artifacts (gitignored)
├── twinship-core-complete.ttl          # All modules merged
├── twinship-core-complete-viz.ttl      # Merged + domain/range for viz
└── twinship-core-complete-docs-viz.ttl # Filtered + viz for documentation
```

## File Descriptions

### Core Files

1. **twinship-base.ttl** (166 lines) - **Foundation Layer**
   - Base classes: `TwinShipInanimatePhysicalObject`, `EnergySystem`
   - Base properties: `TwinShipDataProperties`, `twinshipObjectProperties`
   - Object properties: `componentOf`, `hasComponent`, `ownedBy`
   - Organizational classes: `Organization`, `Fleet`, `Pms`
   - IDO extensions and annotations
   - **Import this + specific modules for modular development**

2. **twinship-core.ttl** (15 lines) - **Complete Aggregate**
   - Minimal file that imports `twinship-base` + all domain modules
   - Provides the complete TwinShip ontology
   - **Import this for the full ontology**

### Domain Modules

3. **modules/vessel.ttl** (1134 lines)
   - Vessel types: `VesselSystem`, `RoRo`, `RoPax`, `Tanker`
   - Hull properties: displacement, draft (aft, fore, mid port/starboard), depth of water
   - Engine systems: `EngineSystem`, `MainEngineSystem`, `AuxiliaryEngineSystem`
   - Engine types: `DieselEngine`, `FourStroke`, `TwoStroke`, `Boiler`
   - Propulsion: `PropellerSystem`, `CPP`, `FPP`
   - Transmission: `GearboxSystem`, `DirectDrive`, `Reduction`, `TISO`
   - Power: `ShaftGeneratorSystem`, `RGShaftGenerator`, `PTO`
   - Equipment: `Maneuvering`, `EmergencyEquipment`
   - Fuel: `Fuel` class + individuals (HFO, MGO, MDO)
   - 130+ engine and vessel properties
   - Imports: `twinship-base`

4. **modules/weather-conditions.ttl** — TwinShip-native weather and wind condition module
   - Classes: `WeatherCondition` (subClassOf `TwinShipQuality`), `WindCondition` (subClassOf `WeatherCondition`)
   - Object properties: `hasWeatherCondition` (subPropertyOf `hasQuality`), `hasWindCondition` (subPropertyOf `hasWeatherCondition`)
   - Data properties: `windSpeed`, `windDirection` (`xsd:decimal`)
   - Does **not** import VesselAI, DUL, GeoSPARQL, or OWL-Time
   - IRI: `https://twin-ship.eu/twinship/weather-conditions`
   - Imports: `twinship-base`

5. **modules/operational-modes.ttl** — Canonical module for categorical modes and states
   - Operating states: `OperatingState` with individuals `CruiseState`, `PortState`, `MaintenanceLayupState`, `ManeuveringState`, `DriftState`, `UnknownOperatingState`
   - Engine modes: `EngineMode`
   - Draft modes: `DraftMode` with individuals `BallastDraft`, `LadenDraft`, `PartLoadDraft`; `TrimMode`; `DraftTrimMode` with individuals `EvenKeel`, `SternTrim`, `BowTrim`, `OptimalTrim`
   - Object properties: `hasOperatingState`, `hasEngineMode`, `hasDraftMode`, `hasTrimMode`, `hasDraftTrimMode`
   - All mode/state classes extend `TwinShipQuality`
   - IRI: `https://twin-ship.eu/twinship/operational-modes`
   - Imports: `twinship-base`

6. **modules/operational-context.ttl** — Canonical module for operational context and voyage data
   - Process classes: `Voyage`, `VoyageLeg` (extend `TwinShipProcess`); `Route`, `Port` (extend `TwinShipInformationObject`)
   - Statistical/profile classes: `OperationalProfile`, `SpeedBin`, `FrequencyDistribution`, `FuelConsumptionSummary`, `FuelConsumptionEstimate`, `FuelConsumptionGapAnalysis`, `PerformanceDeviation`
   - Observation class: `FuelConsumptionObservation` (extends `TwinShipQuality`)
   - Object properties: voyage structure, profile/statistics, fuel, context links
   - Data properties: voyage times/IDs, state statistics, engine observations, speed bins, fuel consumption
   - IRI: `https://twin-ship.eu/twinship/operational-context`
   - Imports: `twinship-base`, `operational-modes`, `weather-conditions`

## Import Patterns

### For Complete Ontology (Most Users)

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix tws: <https://twin-ship.eu/> .

<http://example.org/myOntology> a owl:Ontology ;
    owl:imports <https://twin-ship.eu/twinship/core> .  # Gets everything
```

### For Modular Development

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<http://example.org/myVesselExtension> a owl:Ontology ;
    owl:imports <https://twin-ship.eu/twinship/base>,      # Foundation
                <https://twin-ship.eu/twinship/vessel> .    # Just vessel module
```

### For New TwinShip Modules

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<https://twin-ship.eu/twinship/myNewModule> a owl:Ontology ;
    owl:imports <https://twin-ship.eu/twinship/base> .  # Only import base
```

## Design Pattern

TwinShip uses **OWL restriction-based modelling**: property usage on classes is declared with `owl:someValuesFrom` restrictions on the class rather than `rdfs:domain` on the property. `rdfs:range` is required on all properties. `rdfs:domain` assertions are never written manually — they are synthesized by the build pipeline from the restriction patterns for WIDOCO/WebVOWL compatibility.

### Why not rdfs:domain?

`rdfs:domain :hasQuality :VesselSystem` would cause a reasoner to infer that *any* subject of `:hasQuality` is a `:VesselSystem`, including `VoyageLeg` or `Port`. Restrictions are scoped to the class they are declared on, so they express intent without triggering global inference.

### Pattern

Every class in every module must declare `rdfs:subClassOf` restrictions for all object and data properties characteristic of it. Use `owl:someValuesFrom` for both:

```turtle
:MyClass a owl:Class ;
    rdfs:subClassOf :TwinShipQuality ,
        [ a owl:Restriction ;
          owl:onProperty :hasRelatedThing ;
          owl:someValuesFrom :RelatedClass ],
        [ a owl:Restriction ;
          owl:onProperty :twMyDataProperty ;
          owl:someValuesFrom xsd:decimal ] .
```

What Protégé shows as "subclass of `twinship my data property`" is one of these anonymous restriction classes — not a direct class-to-property relationship. The build script `generate_viz_ontology.py` reads these restrictions to synthesize `rdfs:domain` in the visualization output; a missing restriction means the property will not appear in the WebVOWL graph.

### Concrete example (from vessel.ttl)

```turtle
:Boiler rdfs:subClassOf
    [ a owl:Restriction ; owl:onProperty :consume             ; owl:someValuesFrom :Fuel        ],
    [ a owl:Restriction ; owl:onProperty :twBoilerPowerMaxInKW ; owl:someValuesFrom xsd:double   ],
    [ a owl:Restriction ; owl:onProperty :twBoilerMassInKgPerHr ; owl:someValuesFrom xsd:double  ] .
```

To generate visualization and documentation from the source ontology:

```bash
# Full website generation (documentation + WebVOWL visualization)
./scripts/generate_website.sh --verbose

# Individual steps
uv run python scripts/merge_modules.py --auto model/twinship-core.ttl
uv run python scripts/generate_viz_ontology.py --auto build/twinship-core-complete.ttl
```

## Naming Conventions

All TwinShip entities share a single flat namespace (`https://twin-ship.eu/twinship#`, prefix `:`). Module origin is not encoded in the IRI — it is determined by the file containing the declaration.

### Classes

| Sub-pattern | Convention | Examples |
|---|---|---|
| Foundation / base | `TwinShip` + PascalCase | `:TwinShipQuality`, `:TwinShipProcess`, `:TwinShipInanimatePhysicalObject` |
| Domain-specific | Plain PascalCase | `:VesselSystem`, `:OperatingState`, `:Voyage`, `:WeatherCondition` |
| Industry acronyms | ALL-CAPS | `:CPP`, `:FPP`, `:PTO`, `:RoPax` |

The `TwinShip` prefix marks a class as a broad reusable base. All domain-specific classes extend one of these bases and drop the prefix.

### Object Properties

All object properties use **lowerCamelCase**. The dominant idiom is `has<Thing>`. The property hierarchy root anchor (`:twinshipObjectProperties`) is the only object property that carries the `twinship` prefix.

```turtle
:hasOperatingState, :hasWeatherCondition, :followsRoute, :summarisesVoyage
```

### Data Properties

All data properties use the **`tw` prefix** (two-character lowercase abbreviation of "twinship"), followed by an UpperCamelCase descriptive name, with an optional unit suffix.

```
:tw<DescriptiveName>[In<Unit>]
```

**Examples:**

| Property | Range | Notes |
|---|---|---|
| `:twBoilerPowerMaxInKW` | `xsd:decimal` | Unit suffix `InKW` |
| `:twVoyageDurationHours` | `xsd:decimal` | Unit embedded in name |
| `:twWindSpeed` | `xsd:decimal` | No unit suffix (unit varies by dataset) |
| `:twVoyageIdentifier` | `xsd:string` | No unit suffix (string identifier) |
| `:twVoyageStartTime` | `xsd:dateTime` | No unit suffix (temporal) |
| `:twRecordCount` | `xsd:integer` | No unit suffix (dimensionless count) |

**Unit suffix conventions** (from `vessel.ttl`):
- `InM` — metres; `InKW` — kilowatts; `InMT` — metric tonnes; `InDegC` — degrees Celsius
- `InRevPerMin` — RPM; `KgPerHr` — kg/hr; `KJPerKg` — kJ/kg
- Omit suffix for dimensionless ratios, counts, string identifiers, and `xsd:dateTime` properties

**`rdfs:label`** for data properties must follow `"twinship <descriptive name>"` (lowercase), matching the established pattern in `vessel.ttl`:
```turtle
:twVoyageDurationHours rdfs:label "twinship voyage duration hours" .
:twWindSpeed          rdfs:label "twinship wind speed"@en .
```

### Named Individuals

| Sub-pattern | Convention | Examples |
|---|---|---|
| Descriptive names | PascalCase | `:CruiseState`, `:EvenKeel`, `:SternTrim`, `:OptimalTrim` |
| Industry abbreviations | ALL-CAPS | `:HFO`, `:MGO`, `:MDO` |

### Ontology IRIs

Module ontology IRIs use **kebab-case** path segments under `https://twin-ship.eu/twinship/`:

```
https://twin-ship.eu/twinship/base
https://twin-ship.eu/twinship/vessel
https://twin-ship.eu/twinship/weather-conditions
https://twin-ship.eu/twinship/operational-modes
https://twin-ship.eu/twinship/operational-context
```

Version IRIs append `/<semver>`, e.g., `https://twin-ship.eu/twinship/base/0.0.4`.

## Upper Ontology (TOP)

TwinShip uses **IDO (ISO 15926-14)** as the upper ontology:
- File: `external/IDO_20240503.ttl`
- URI: `http://rds.posccaesar.org/ontology/lis14/ont/core/1.0`
- Key classes: `ido:InanimatePhysicalObject`, `ido:Object`

All TwinShip physical entities inherit from `TwinShipInanimatePhysicalObject` which extends `ido:InanimatePhysicalObject`.

## External Dependencies

### VesselAI (External Reference Only)
- **Location**: `external/vesselai/vesselAI_ontology_v2.owl`
- **URI**: `http://www.vesselAI-project.eu/vesselai`
- **Upper Ontology**: DUL (DOLCE+DnS Ultralite)
- **Status**: **Not imported** by any TwinShip module. Retained for inspection and reference only.
- **Rationale**: VesselAI is DUL-based; TwinShip uses IDO (ISO 15926-14). The upper ontologies are categorially incompatible — e.g., VesselAI `Vessel` is a `dul:Agent` while TwinShip `VesselSystem` is an `ido:InanimatePhysicalObject`. Selected TwinShip terms carry `rdfs:seeAlso` annotations pointing to related VesselAI terms for traceability. See `docs/ontology/vesselai-full-reuse-audit.txt` for the full design decision.

### QUDT
- **Purpose**: Quantities, units, and dimensions
- **Files**: 
  - Schema: `external/SCHEMA_QUDT-simplified.ttl`
  - Quantity Kinds: `vocabularies/VOCAB_QUDT-QUANTITY-KINDS-simplified.ttl`
  - Units: `vocabularies/VOCAB_QUDT_UNIT2-simplified.ttl`

### PAV
- **Purpose**: Provenance metadata
- **File**: `external/PAV-simplified.ttl`

## Catalog File

`catalog-v001.xml` maps ontology URIs to local files for Protégé and other tools:

```xml
<!-- TwinShip Ontologies -->
<uri name="https://twin-ship.eu/twinship/base" uri="twinship-base.ttl"/>
<uri name="https://twin-ship.eu/twinship/core" uri="twinship-core.ttl"/>
<uri name="https://twin-ship.eu/twinship/vessel" uri="modules/vessel.ttl"/>
<uri name="https://twin-ship.eu/twinship/weather-conditions" uri="modules/weather-conditions.ttl"/>

<!-- External Ontologies -->
<!-- VesselAI: retained for reference only; not used by owl:imports -->
<uri name="http://www.vesselAI-project.eu/vesselai" uri="external/vesselai/vesselAI_ontology_v2.owl"/>
<uri name="http://rds.posccaesar.org/ontology/lis14/ont/core/1.0" uri="external/IDO_20240503.ttl"/>
<uri name="http://qudt.org/schema/qudt/" uri="external/SCHEMA_QUDT-simplified.ttl"/>
```

This enables Protégé and other tools to resolve `owl:imports` statements to local files instead of fetching from the web.
## Adding New Modules

The `modules/` directory contains four fully implemented modules. To add a new module:

1. Create `model/modules/<name>.ttl` with `owl:imports <https://twin-ship.eu/twinship/base>`
2. Add a URI mapping entry to `model/catalog-v001.xml`
3. Add `owl:imports <https://twin-ship.eu/twinship/<name>>` to `model/twinship-core.ttl`
4. Run `./scripts/generate_website.sh` to verify integration

## Version Information

- **Version**: 0.0.4
- **Created**: 2025-01-21
- **Last Updated**: 2026-05-21

## Usage Examples

### Load in Protégé
Open `model/twinship-core.ttl` - the catalog will automatically resolve all imports to local files.

### Query with SPARQL
```sparql
PREFIX : <https://twin-ship.eu/twinship#>
PREFIX ido: <http://rds.posccaesar.org/ontology/lis14/rdl/>

SELECT ?vessel ?name WHERE {
    ?vessel a :VesselSystem ;
            rdfs:label ?name .
}
```

### Generate Documentation
```bash
./scripts/generate_website.sh --verbose
```

This creates:
- `build/twinship-core-complete.ttl` — All modules merged
- `build/twinship-core-complete-docs-viz.ttl` — Documentation-friendly build
- `docs/website/documentation/index-en.html` — WIDOCO HTML documentation
- `docs/website/documentation/webvowl/` — WebVOWL interactive visualization
- `docs/website/index.html` — Landing page

## License

See repository LICENSE file.
