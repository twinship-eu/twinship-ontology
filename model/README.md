# TwinShip Ontology - Model Directory

This directory contains the TwinShip ontology organized in a **modular architecture** with a foundation layer and domain-specific modules.

## Architecture Overview

```
┌─────────────────────────────────────────┐
│     twinship-core.ttl (Complete)        │  ← Import this for full ontology
│     Aggregate of base + all modules     │
└─────────────────┬───────────────────────┘
                  │ imports
        ┌─────────┴─────────┬──────────────────┬────────────┐
        ▼                   ▼                  ▼            ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────┐  ┌────────┐
│ twinship-base │  │ modules/        │  │ modules/ │  │modules/│
│  (Foundation) │  │ engine.ttl      │  │ hull.ttl │  │ ...    │
│               │◄─┤ Propulsion,     │◄─┤ Vessel   │◄─┤ Weather│
│ Base classes, │  │ Fuel, Gearbox   │  │ types    │  │        │
│ properties    │  │                 │  │          │  │        │
└───────────────┘  └─────────────────┘  └──────────┘  └────────┘
        │
        │ imports
        ▼
┌──────────────────────────────────────────────────────┐
│  External Ontologies: IDO, PAV, QUDT, VesselAI      │
└──────────────────────────────────────────────────────┘
```

## Directory Structure

```
model/                         # Source ontology files (version controlled)
├── twinship-base.ttl          # Foundation ontology (base classes, properties)
├── twinship-core.ttl          # Complete aggregate (imports base + all modules)
├── modules/                   # Domain-specific modules
│   ├── engine.ttl            # Engine, propulsion, fuel, gearbox
│   ├── hull.ttl              # Vessel types, hull properties
│   ├── weatherconditions.ttl # Weather-related classes
│   └── draft_time_mode.ttl   # (Placeholder for future development)
├── external/                  # External ontology dependencies
│   ├── IDO_20240503.ttl      # ISO 15926-14 upper ontology
│   ├── PAV-simplified.ttl    # Provenance, Authoring and Versioning
│   ├── SCHEMA_QUDT-simplified.ttl
│   └── vesselai/             # VesselAI v2 ontology
├── vocabularies/              # QUDT vocabularies
│   ├── VOCAB_QUDT-QUANTITY-KINDS-simplified.ttl
│   └── VOCAB_QUDT_UNIT2-simplified.ttl
└── catalog-v001.xml           # Protégé catalog for URI resolution

build/                         # Auto-generated build artifacts (gitignored)
├── twinship-core-complete.ttl        # All modules merged
├── twinship-core-complete-viz.ttl    # Merged + domain/range for viz
└── twinship-core-complete-docs-viz.ttl # Filtered + viz for documentation
```

## File Descriptions

### Core Files

1. **twinship-base.ttl** (166 lines) - **Foundation Layer**
   - Base classes: `TwinShipInanimatePhysicalObject`, `EnergySystem`
   - Base properties: `TwinShipDataProperties`, `twinshipObjectProperties`
   - Object properties: `componentOf`, `hasComponent`, `ownedBy`, `associatedEntity`
   - Organizational classes: `Organization`, `Fleet`, `Pms`
   - IDO extensions and annotations
   - **Import this + specific modules for modular development**

2. **twinship-core.ttl** (15 lines) - **Complete Aggregate**
   - Minimal file that imports `twinship-base` + all domain modules
   - Provides the complete TwinShip ontology
   - **Import this for the full ontology**

### Domain Modules

3. **modules/engine.ttl** (1074 lines)
   - Engine systems: `EngineSystem`, `MainEngineSystem`, `AuxiliaryEngineSystem`
   - Engine types: `DieselEngine`, `FourStroke`, `TwoStroke`, `Boiler`
   - Propulsion: `PropellerSystem`, `CPP`, `FPP`
   - Transmission: `GearboxSystem`, `DirectDrive`, `Reduction`, `TISO`
   - Power: `ShaftGeneratorSystem`, `RGShaftGenerator`, `PTO`
   - Equipment: `Maneuvering`, `EmergencyEquipment`
   - Fuel: `Fuel` class + individuals (HFO, MGO, MDO)
   - 130+ engine-related properties
   - Imports: `twinship-base`

4. **modules/hull.ttl** (99 lines)
   - Vessel types: `VesselSystem`, `RoRo`, `RoPax`, `Tanker`
   - Hull properties: displacement, draft (aft, fore, mid port/starboard), depth of water
   - Imports: `twinship-base`

## Import Patterns

### For Complete Ontology (Most Users)

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix tws: <https://twin-ship.eu/> .

<http://example.org/myOntology> a owl:Ontology ;
    owl:imports <https://twin-ship.eu/twinship-core> .  # Gets everything
```

### For Modular Development

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<http://example.org/myEngineExtension> a owl:Ontology ;
    owl:imports <https://twin-ship.eu/twinship-base>,      # Foundation
                <https://twin-ship.eu/modules/engine> .     # Just engine module
```

### For New TwinShip Modules

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<https://twin-ship.eu/modules/myNewModule> a owl:Ontology ;
    owl:imports <https://twin-ship.eu/twinship-base> .  # Only import base
```

## Design Pattern
Use `core/twinship-core.ttl` or import via `twinship-core.ttl`

**Fortwinship-core.ttl` directly
Use the scripts to generate simplified versions:

```bash
# Generate visualization-friendly version (converts restrictions to domain/range)
python scripts/generate_viz_ontology.py --auto model/core/twinship-core.ttl

# Generate complete documentation
./scripts/generate_docs.sh --source model/twinship-core.ttl
```

## Upper Ontology (TOP)

TwinShip uses **IDO (ISO 15926-14)** as the upper ontology:
- File: `external/IDO_20240503.ttl`
- URI: `http://rds.posccaesar.org/ontology/lis14/ont/core/1.0`
- Key classes: `ido:InanimatePhysicalObject`, `ido:Object`

All TwinShip physical entities inherit from `TwinShipInanimatePhysicalObject` which extends `ido:InanimatePhysicalObject`.

## External Dependencies

### VesselAI
- **Purpose**: Weather and environmental conditions
- **Location**: `external/vesselai/vesselAI_ontology_v2.owl`
- **URI**: `http://www.vesselAI-project.eu/vesselai`
- **Upper Ontology**: DUL (DOLCE+DnS Ultralite)
- **Note**: VesselAI uses a different upper ontology than TwinShip, but this is acceptable for vocabulary reuse

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
<uri name="https://twin-ship.eu/ontology" uri="twinship-base.ttl"/>
<uri name="https://twin-ship.eu/ontology/core" uri="twinship-core.ttl"/>
<uri name="https://twin-ship.eu/ontology/modules/engine" uri="modules/engine.ttl"/>
<uri name="https://twin-ship.eu/ontology/modules/hull" uri="modules/hull.ttl"/>

<!-- External Ontologies -->
<uri name="http://www.vesselAI-project.eu/vesselai" uri="external/vesselai/vesselAI_ontology_v2.owl"/>
<uri name="http://rds.posccaesar.org/ontology/lis14/ont/core/1.0" uri="external/IDO_20240503.ttl"/>
<uri name="http://qudt.org/schema/qudt/" uri="external/SCHEMA_QUDT-simplified.ttl"/>
```

This enables Protégé and other tools to resolve `owl:imports` statements to local files instead of fetching from the web.
## Future Modularization

The `modules/` directory contains placeholders for future modularization efforts. The current approach keeps the complete ontology in `core/twinship-core.ttl` due to the complexity of splitting restriction-based definitions.

When ready to modularize:
1. Extract domain-specific classes to modules
2. Extract related properties
3. Update imports in `twinship-core.ttl`
4. Use `scripts/merge_modules.py` to generate complete version for distribution

## Version Information

- **Version**: 0.0.1
- **Created**: 2025-01-21
- **Last Updated**: 2026-02-04

## Usage Examples

### Load in Protégé
Open `model/twinship-core.ttl` - the catalog will automatically resolve all imports to local files.

### Query with SPARQL
```sparql
PREFIX : <https://twin-ship.eu/>
PREFIX ido: <http://rds.posccaesar.org/ontology/lis14/rdl/>

SELECT ?vessel ?name WHERE {
    ?vessel a :VesselSystem ;
            rdfs:label ?name .
}
```

### Generate Documentation
```bash
cd /Users/elvesater/GitHub/twinship-eu/twinship-ontology
./scripts/generate_docs.sh --source model/twinship-core.ttl --verbose
```

This creates:
- `model/twinship-core-complete.ttl` - All imports merged
- `model/twinship-core-complete-viz.ttl` - Visualization-friendly (domain/range)
- `docs/ontology/index.html` - HTML documentation

## License

See repository LICENSE file.
