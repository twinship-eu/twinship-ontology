# TwinShip Competency Questions

36 competency questions (CQs) defining the scope and answerable queries of the
TwinShip ontology. Source: deliverable D3.4.

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
| CQ-32 | For an unmanned RoRo vessel, what superstructure and hull parameters can be modified (e.g., removing bridge and hotel infrastructure), and how does this affect the Hotel Load power requirements? | 🔲 | — |
| CQ-33 | What Wind Assisted Propulsion System or Dynamic Wing configurations are modelled for a future unmanned RoRo, and what renewable energy contribution (kW) do they provide? | 🔲 | — |

---

## System Connectivity & Integration

*Purpose: Support energy routing and electrical integration.*

| CQ No. | Competency Question | Status | Test file |
|--------|---------------------|--------|-----------|
| CQ-34 | Which systems are connected to the main switchboard (e.g., Gen Set System, Energy Storage System, Frequency Converter System, Shaft Generator System)? | 🔲 | — |
| CQ-35 | What Bidirectional Converter System nominal voltage and max current are defined for the DC bus, enabling ESS integration? | 🔲 | — |
| CQ-36 | What are the documented API interfaces of the Digital Twin, and which third-party systems are they compatible with? | 🔲 | — |
