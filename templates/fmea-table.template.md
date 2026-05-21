---
diagram_type: fmea_table
fmea_type: process
language: en
---

# Process FMEA: Optical Module Assembly

Goal: Identify critical assembly risks, calculate RPN from S/O/D scores, and prioritize corrective actions.
Project: Optical Module Pilot Build
Review Frequency: Weekly during pilot build
Last Review Date: 2026-05-21
Note: Keep each row focused on one failure mode.
Note: Update occurrence and detection scores after corrective actions are verified.

## Row F1

Item / Function: Optical alignment
Icon: aperture
Failure Mode: Coupling efficiency below target
Effects:
- Low output power
- First-pass yield loss
Causes:
- Fixture repeatability drift
- Adhesive shrinkage after cure
Prevention Controls:
- Daily fixture check
- Qualified adhesive profile
Detection Controls:
- Before-and-after coupling check
- Final optical power test
Severity: 8
Occurrence: 5
Detection: 5
Recommended Actions:
- Add alignment fixture GRR review
- Track coupling shift by adhesive lot
Owner: Process Eng
Target Completion: 2026-06-10
Status: Open

## Row F2

Item / Function: Laser drive setup
Icon: circuit-board
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
Owner: Test Eng
Target Completion: 2026-06-05
Status: In Progress

## Row F3

Item / Function: Thermal interface assembly
Icon: thermometer
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
Owner: ME
Target Completion: 2026-06-18
Status: Open
