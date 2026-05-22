---
diagram_type: fmea_table
fmea_type: process
language: en
---

# Process FMEA: Optical Module Pilot Assembly

Goal: Identify process failure modes that could reduce first-pass yield or create reliability risk before the next pilot build.
Project: Optical Module Pilot Build
Owner: Quality Engineering
Review Frequency: Weekly during pilot production
Note: Use one row per failure mode and keep actions concise.

## Row F1

Item / Function: Active optical alignment
Failure Mode: Coupling efficiency below target
Effects:
- Low output power
- First-pass yield loss
Causes:
- Alignment fixture repeatability drift
- Adhesive shrinkage after cure
Prevention Controls:
- Daily fixture verification
- Qualified adhesive cure profile
Detection Controls:
- Before-and-after coupling review
- Final optical power test
Severity: 8
Occurrence: 5
Detection: 5
Recommended Actions:
- Add fixture GRR review
- Track coupling shift by adhesive lot
Owner: Process Engineering
Target Completion: 2026-06-10
Status: Open

## Row F2

Item / Function: Laser drive setup
Failure Mode: Incorrect drive current limit
Effects:
- Power instability
- Premature device stress
Causes:
- Outdated work instruction
- Wrong firmware compensation setting
Prevention Controls:
- Released work instruction
- Firmware version control
Detection Controls:
- ATE current log review
- Operator checklist
Severity: 7
Occurrence: 4
Detection: 4
Recommended Actions:
- Lock approved firmware version in setup screen
- Add first-article current audit
Owner: Test Engineering
Target Completion: 2026-06-05
Status: In Progress

## Row F3

Item / Function: Thermal interface assembly
Failure Mode: Poor thermal contact
Effects:
- Higher laser temperature
- Reliability margin reduction
Causes:
- Uneven TIM thickness
- Insufficient clamp force
Prevention Controls:
- Torque-controlled assembly
- TIM thickness specification
Detection Controls:
- Thermal resistance sample check
- Visual inspection
Severity: 9
Occurrence: 3
Detection: 5
Recommended Actions:
- Add thermal resistance gate for pilot lots
- Review clamp tooling wear
Owner: Mechanical Engineering
Target Completion: 2026-06-18
Status: Planned

## Row F4

Item / Function: Optical surface handling
Failure Mode: Contamination on optical surface
Effects:
- Insertion loss increase
- Unstable coupling margin
Causes:
- Exposed lens handling
- Incomplete cleaning confirmation
Prevention Controls:
- Covered transfer trays
- Approved cleaning procedure
Detection Controls:
- Microscope inspection
- Near-field image review
Severity: 7
Occurrence: 4
Detection: 3
Recommended Actions:
- Add handling audit points
- Update cleaning checklist
Owner: Manufacturing Engineering
Target Completion: 2026-06-12
Status: Open

## Row F5

Item / Function: Final packing traceability
Failure Mode: Label data mismatch
Effects:
- Shipment hold
- Traceability rework
Causes:
- Manual label entry
- Late traveler updates
Prevention Controls:
- Traveler release review
- Barcode template control
Detection Controls:
- Barcode scan at pack-out
- QA sampling
Severity: 4
Occurrence: 3
Detection: 3
Recommended Actions:
- Link traveler data to barcode generation
Owner: Quality
Target Completion: 2026-06-20
Status: Planned
