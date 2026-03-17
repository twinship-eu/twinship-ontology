# TwinShip Ontology — Statistics

> **Version:** 0.0.4  
> **Ontology last updated:** 2026-03-03  
> **Statistics generated:** 2026-03-17  
> **Source:** `build/twinship-core-complete-docs-viz.ttl`

## Summary

| Metric              | Count | Illustrative examples |
| ------------------- | ----- | --------------------- |
| Classes             | 58    | TwinShipInanimatePhysicalObject<br>MainEngineSystem<br>PropellerSystem<br>ShaftGeneratorSystem<br>Boiler<br>GenSetSystem<br>Fuel<br>VesselSystem<br>EnergyStorageSystem<br>AuxiliaryEngineSystem |
| Object properties   | 8     | componentOf<br>connectedTo<br>consume<br>directlyConnectedTo<br>hasComponent<br>ownedBy<br>partOf<br>twinshipObjectProperties |
| Data properties     | 170   | twDieselEnginePowerMaxInKW<br>twDieselEngineSpeedInRevPerMin<br>twEMPowerInMWh<br>twFCFrequencyInHz<br>twFCVoltageInVolts<br>twGeneratorPowerMaxInKW<br>twGeneratorSpeedInRevPerMin<br>twShaftPowerMaxInKW<br>twShaftSpeedMaxInRevPerMin<br>twShaftTorqueMaxInKnm |
| Imported ontologies | 5     | IDO (LIS14)<br>PAV<br>QUDT QuantityKind<br>QUDT Unit<br>VesselAI (DUL/Time) |

## Object Properties

*8 properties — all listed below*

| Property                   | Namespace | Label                      | Description |
| -------------------------- | --------- | -------------------------- | ----------- |
| `componentOf`              | TwinShip  | component of               | Relates a component to the ship or system it is part of. |
| `connectedTo`              | IDO       | connectedTo                |  |
| `consume`                  | TwinShip  | consumes                   | Relates an engine or system to the fuel it consumes. |
| `directlyConnectedTo`      | IDO       | directly connected to      | Relates two inanimate physical objects that are directly connected. |
| `hasComponent`             | TwinShip  | has component              | Relates a ship or system to a component that is part of it. |
| `ownedBy`                  | TwinShip  | owned by                   | Relates an entity to its owner (typically an Organization). |
| `partOf`                   | IDO       | partOf                     |  |
| `twinshipObjectProperties` | TwinShip  | twinship object properties | Parent property for all TwinShip-specific object properties. |

## Imported Ontologies

| Ontology            | URI |
| ------------------- | --- |
| IDO (LIS14)         | <http://rds.posccaesar.org/ontology/lis14/ont/core/1.0> |
| PAV                 | <http://purl.org/pav/> |
| QUDT QuantityKind   | <http://qudt.org/vocab/quantitykind/> |
| QUDT Unit           | <http://qudt.org/vocab/unit/> |
| VesselAI (DUL/Time) | <http://www.vesselAI-project.eu/vesselai> |
