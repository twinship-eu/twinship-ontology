# TwinShip Ontology — Statistics

> **Version:** 0.0.4  
> **Ontology last updated:** 2026-03-03  
> **Statistics generated:** 2026-10-02  
> **Source:** `build/twinship-core-complete-docs-viz.ttl`

## Summary

| Metric              | Count | Illustrative examples |
| ------------------- | ----- | --------------------- |
| Classes             | 212   | TwinShipInformationObject<br>Voyage<br>TwinShipInanimatePhysicalObject<br>VoyageLeg<br>MainEngineSystem<br>Fuel<br>PropellerSystem<br>ShaftGeneratorSystem<br>GenSetSystem<br>EngineSystem |
| Object properties   | 88    | hasInformationObject<br>twinshipObjectProperties<br>hasQuality<br>hasProcess<br>hasWeatherCondition<br>connectedTo<br>documentsModel<br>hasComponent<br>hasEstimation<br>hasLoadingCondition |
| Data properties     | 237   | twMeanSpeedInKnots<br>twNumericValue<br>twDieselEnginePowerMaxInKW<br>twDieselEngineSpeedInRevPerMin<br>twDistanceInNm<br>twEMPowerInMWh<br>twEngineLoadPercentage<br>twEngineSpeedInRevPerMin<br>twEstimatedMeanFuelConsumption<br>twExecutionTime |
| Imported ontologies | 5     | IDO (LIS14)<br>PAV<br>QUDT QuantityKind<br>QUDT Unit<br>qudt-vocabulary |

## Object Properties

*88 properties — showing 10 examples above*

- `componentOf`
- `connectedTo`
- `consume`
- `contributedFeature`
- `describesDataset`
- `directlyConnectedTo`
- `documentsModel`
- `estimatesFeature`
- `followsRoute`
- `hasArrivalPort`
- `hasAssumption`
- `hasComponent`
- `hasCurrentCondition`
- `hasDeparturePort`
- `hasDraftCondition`
- `hasDraftMode`
- `hasDraftTrimMode`
- `hasEndWayPoint`
- `hasEngineMode`
- `hasEngineSpeedBin`
- `hasEstimation`
- `hasFeatureContribution`
- `hasFrequencyDistribution`
- `hasFuelConsumptionObservation`
- `hasFuelConsumptionSummary`
- `hasInformationObject`
- `hasLoadingCondition`
- `hasLoadingPreset`
- `hasModelCard`
- `hasObservationResult`
- `hasOperatingState`
- `hasOperationalProfile`
- `hasPart`
- `hasPerformanceDeviation`
- `hasPerformanceModel`
- `hasPerformanceStatistics`
- `hasPrediction`
- `hasPredictionResult`
- `hasProcess`
- `hasQuality`
- `hasQuantityAngle`
- `hasQuantityElectricCurrent`
- `hasQuantityElectricPotential`
- `hasQuantityEnergy`
- `hasQuantityForce`
- `hasQuantityFrequency`
- `hasQuantityLength`
- `hasQuantityMass`
- `hasQuantityMassDensity`
- `hasQuantityMassFlowRate`
- `hasQuantityMassRatio`
- `hasQuantityPower`
- `hasQuantityPressure`
- `hasQuantityRatio`
- `hasQuantityRotationalVelocity`
- `hasQuantitySpecificEnergy`
- `hasQuantitySpeed`
- `hasQuantityTemperature`
- `hasQuantityTime`
- `hasQuantityTorque`
- `hasQuantityVolume`
- `hasQuantityVolumeFlowRate`
- `hasSpeedBin`
- `hasSpeedReference`
- `hasStartWayPoint`
- `hasTrimCondition`
- `hasTrimMode`
- `hasVersion`
- `hasVoyage`
- `hasVoyageLeg`
- `hasWaveCondition`
- `hasWeatherCondition`
- `hasWindCondition`
- `isEstimationForVoyageLeg`
- `isPredictionForVoyageLeg`
- `observedDuringVoyage`
- `observedDuringVoyageLeg`
- `ownedBy`
- `partOf`
- `predictsFeature`
- `summarisesOperatingState`
- `summarisesVoyage`
- `trainedOnDataset`
- `twObservedQuality`
- `twinshipObjectProperties`
- `usesObservation`
- `wasGeneratedByEstimationProcess`
- `wasGeneratedByPredictionProcess`

## Imported Ontologies

| Ontology          | URI |
| ----------------- | --- |
| IDO (LIS14)       | <http://rds.posccaesar.org/ontology/lis14/ont/core/1.0> |
| PAV               | <http://purl.org/pav/> |
| QUDT QuantityKind | <http://qudt.org/vocab/quantitykind/> |
| QUDT Unit         | <http://qudt.org/vocab/unit/> |
| qudt-vocabulary   | <https://twin-ship.eu/twinship/qudt-vocabulary> |
