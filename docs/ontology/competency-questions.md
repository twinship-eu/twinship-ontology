# TwinShip Competency Questions

36 competency questions (CQs) defining the scope and answerable queries of the
TwinShip ontology. Source: deliverable D3.4.
The ontology statisical extension contains 32 CQs which are listed below as CQE-XX. The scope is derived from TwinShip-D1-1-APR28-User Requirements and DT-DSS Functional Specifications-v2.0 from three user-stories. 

**Status values:** ✅ Covered · ⚠️ Partial · ❌ Not yet covered · 🔲 Not assessed

Each CQ that is implemented as a SPARQL test has a corresponding `.rq` file
under [`tests/competency/`](../../tests/competency/).

---

## Vessel & Fleet Structure

*Purpose: Identify vessels, their characteristics, and fleet membership.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ-01 | Which vessels of type RoRo, RoPax, or Tanker belong to a given fleet? | 🔲 | — |
| CQ-02 | What is the maximum displacement (in MT) of each VesselSystem in the fleet? | 🔲 | — |
| CQ-03 | What are the maximum draft values (aft, fore, mid-port, mid-starboard) for a specific vessel? | 🔲 | — |
| CQ-04 | What Efficiency Enhancement System components (GateRudder, AirLubricationSystem, SuctionSail, DynamicWing) are installed on each vessel? | 🔲 | — |

---

## Propulsion & Engine Configuration

*Purpose: Capture mechanical configuration and propulsion architecture.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ-05 | What is the propulsion configuration of a vessel — Mechanical (direct drive) or Diesel‑Electric? | 🔲 | — |
| CQ-06 | What type of main engine (TwoStroke or FourStroke) is installed, and what is its maximum power (kW) and rated speed (RPM)? | 🔲 | — |
| CQ-07 | What Propeller System type (FPP or CPP) is fitted to each vessel, and what are its key parameters (diameter, pitch/diameter ratio, number of blades, efficiency)? | 🔲 | — |
| CQ-08 | Is a Gearbox System present, and what is the gearbox ratio and efficiency for each vessel? | 🔲 | — |
| CQ-09 | What is the maximum shaft power (kW), torque (kNm), and speed (RPM) for the propulsion shaft? | 🔲 | — |
| CQ-10 | Which vessels use a Shaft Generator System, and what is its maximum power output? | 🔲 | — |

---

## Energy & Fuel Consumption

*Purpose: Support sustainability and emissions calculations.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ-11 | What fuels does each Marine Engine System consume (via the `consumes` property), and what are their CO₂, CH₄, and NOₓ emission factors (g/kg of fuel)? | 🔲 | — |
| CQ-12 | What is the current fuel consumption rate (MT/hr) and total fuel consumption (MT) for each vessel's Main Engine System and Auxiliary Engine System? | 🔲 | — |
| CQ-13 | What is the Lower Heating Value (LHV in kJ/kg) and sulphur content (%) of each Fuel type used across the fleet? | 🔲 | — |
| CQ-14 | Does any vessel use ammonia (AMM) or bio-fuel (BF) as a fuel, and what is its power capacity for such marine engine System? | 🔲 | — |
| CQ-15 | What is the total propulsion power (kW) and auxiliary load power (hotel load + ship services) for each vessel? | 🔲 | — |

---

## Efficiency Enhancement Technologies

*Purpose: Model energy-saving devices and their impact.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ-16 | What is the power reduction efficiency (%) of the Air Lubrication System fitted to a vessel? | 🔲 | — |
| CQ-17 | What is the power output (kW) and efficiency (%) of any Gate Rudder installed? | 🔲 | — |
| CQ-18 | What is the power (kW) and efficiency reduction (%) achieved by the Dynamic Wing system? | 🔲 | — |
| CQ-19 | What is the power (kW) and efficiency (%) of the Wind Assisted Propulsion System (e.g., SuctionSail)? | 🔲 | — |
| CQ-20 | Which vessels have no Efficiency Enhancement System components and are therefore candidates for retrofitting? | 🔲 | — |

---

## Emissions & Sustainability (CII / GHG)

*Purpose: Provide the semantic basis for CII/EEXI/GHG analyses.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ-21 | For each vessel, what is the total CO₂ emission rate (g/hr) calculated from fuel consumption and the fuel's CO₂ emission factor? | 🔲 | — |
| CQ-22 | Which vessels have an SCR (Selective Catalytic Reduction) system, and what is its NOₓ reduction efficiency (%) and operating temperature? | 🔲 | — |
| CQ-23 | What is the exhaust gas flow rate (kg/hr) through the SCR catalyst for each main engine? | 🔲 | — |
| CQ-24 | Which vessels in the fleet are consuming MGO, and what is the MGO mass flow rate (kg/hr)? (Supports CII/EEXI compliance) | 🔲 | — |

---

## Energy Storage & Alternative Power

*Purpose: Represent ESS, shore power, and hybrid systems.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ-25 | What Energy Storage System (battery) capacity (MWh), C-rate, depth of discharge (%), and cycle life are available on each vessel? | 🔲 | — |
| CQ-26 | Is any vessel connected to On Shore Power (cold ironing), and for how many hours and at what power (kWh)? (Port-side emissions reduction) | 🔲 | — |

---

## Auxiliary Systems & Loads

*Purpose: Capture additional subsystems and operating loads.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ-27 | What is the hotel load power (kW) and ship services power (kW) for each vessel's Auxiliary Load? | 🔲 | — |
| CQ-28 | What is the Auxiliary Engine System fuel rate (kg/hr) and maximum power (kW) for each vessel? | 🔲 | — |
| CQ-29 | What is the maximum power (kW) of each Bow Thruster, and what fuel does it consume in emergency mode? | 🔲 | — |

---

## Organisational & Fleet Management

*Purpose: Link vessels to owners, fleets, and comparative scenarios.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ-30 | Which Organisation owns a given vessel or fleet, enabling fleet-level performance aggregation? | 🔲 | — |
| CQ-31 | Which vessels in the fleet are of type RoPax, and what are their shared design parameters for comparative retrofitting decisions? | 🔲 | — |

---

## Unmanned / Future Vessel Simulation

*Purpose: Extend ontology toward a futuristic unmanned RoRo concept.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ‑32 | For an unmanned RoRo vessel, what superstructure and hull parameters can be modified (e.g., removing bridge and hotel infrastructure), and how does this affect the Hotel Load power requirements? | 🔲 | — |
| CQ-33 | What Wind Assisted Propulsion System or Dynamic Wing configurations are modelled for a future unmanned RoRo, and what renewable energy contribution (kW) do they provide? | 🔲 | — |

---

## System Connectivity & Integration

*Purpose: Support energy routing and electrical integration.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ-34 | Which systems are connected to the main switchboard (e.g., Gen Set System, Energy Storage System, Frequency Converter System, Shaft Generator System)? | 🔲 | — |
| CQ-35 | What Bidirectional Converter System nominal voltage and max current are defined for the DC bus, enabling ESS integration? | 🔲 | — |
| CQ-36 | What are the documented API interfaces of the Digital Twin, and which third-party systems are they compatible with? | 🔲 | — |

---


# Extension Competency Questions

## Current State and Observations

*Purpose: Adds the observations and time series data that can be used to input for fuel models.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQE‑01 | What are the current fuel consumption and CO₂ emissions of the vessel for the ongoing voyage? | 🔲 | — |
| CQE‑02 | What is the current fuel consumption rate (MT/hr) and total fuel consumption (MT) for each vessel's Main Engine System and Auxiliary Engine System?  | 🔲 | — |
| CQE-03 | Which weather conditions correlate with speed reduction? | 🔲 | — |
| CQE-04 | Which operational parameters influence vessel emissions? | ❌ | — |
| CQE-05 | Which weather conditions contribute to increased vessel energy efficiency | ❌ | — |
| CQE-06 | How do weather conditions affect fuel consumption on Voyage leg and Voyage? | ❌ | — |

---

## Estimation, Prediction and Forecasting

*Purpose: Gives range of what the model should be used for.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQE‑07 | What is the predicted fuel consumption for Voyage? | 🔲 | — |
| CQE-08 | What is the predicted fuel consumption rate (MT/hr) and total fuel consumption (MT) for each vessel's Main Engine System and Auxiliary Engine System? | 🔲 | — |
| CQE-09 | What is the predicted CO₂ emission rate (g/hr) for a vessel during a voyage under the current operational conditions? | 🔲 | — |
| CQE-10 | How would the predicted emissions change if change of engine mode? | 🔲 | — |
| CQE-11 | How do predicted emissions differ between alternative speeds for the remainder of the voyage? | ❌ | — |
| CQE-12 | What are the emissions per nautical mile for each voyage leg? | 🔲 | — |
| CQE-13 | What are the predicted emissions after changing speed for Voyage leg? | ❌ | — |
| CQE-14 | How does the predicted fuel consumption differ between alternative itineraries for the same voyage objective? | ❌ | — |
| CQE-15 | How does Just-in-Time arrival affect predicted fuel consumption and emissions compared to arriving early? | ❌ | — |
| CQE-16 | How do predicted fuel cost and emissions differ between voyage plans satisfying different voyage objectives? | ❌ | — |
| CQE-17 | How do predicted emissions differ between engine operational modes under the same speed condition? | ❌ | — |
| CQE-18 | How do predicted emissions differ between trim/draft configurations? | ❌ | — |


---

## Observation and Prediction Provenance

*Purpose: Adds provarance and documentation to the models used for predictions.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQE-19 | Is the emission value observed or estimated? | ❌ | — |
| CQE-20 | Which prediction belongs to Voyage leg? | 🔲 | — |
| CQE-21 | Which estimation belongs to Voyage? | 🔲 | — |
| CQE-22 | For which voyage leg is the prediction valid? | 🔲 | — |
| CQE-23 | Which statistical model was used to generate a prediction and which input variables were included? | ❌ | — |
| CQE-24 | Which synthetic voyage scenarios were generated for a vessel and what assumptions were used? | ❌ | — |
| CQE-25 | What confidence level /(model parameters) is associated with the predicted fuel consumption for a voyage leg / voyage? | ❌ | — |
| CQE-26 | Which current observations were used to generate a given prediction? | 🔲 | — |
| CQE-27 | Which weather conditions were used to generate the prediction? | 🔲 | — |
| CQE-28 | Which engine operational mode was assumed for the predicted voyage? | 🔲 | — |
| CQE-29 | Which operational parameters contributed to the prediction and to what extent? | ❌ | — |
| CQE-30 | Which dataset was used to train this statistical model? | 🔲 | — |
| CQE-31 | Which version of the statistical model generated this prediction? | 🔲 | — |


---

## Statistical Model Comparison

*Purpose: To compare the different ship performance models.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQE-32 | How do predictions differ between alternative statistical models for the same voyage? | ❌ | — |