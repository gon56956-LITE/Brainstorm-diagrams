---
diagram_type: fmea_table
fmea_type: process
language: en
---

# Process FMEA: Optical Module Pilot Build

Goal: Prioritize assembly and test risks that may reduce first-pass yield.
Project: Pilot Yield Recovery
Review Frequency: Weekly
Last Review Date: 2026-05-21
Note: RPN is calculated as S x O x D.
Note: High risk rows need containment and named owners.

## Row F1

Item / Function: Optical alignment
Failure Mode: Coupling efficiency below target
Effects:
- Low output power
- Yield loss at final test
Causes:
- Alignment fixture repeatability drift
- Adhesive shrinkage after cure
Prevention Controls:
- Daily fixture verification
- Qualified adhesive cure profile
Detection Controls:
- Coupling efficiency check
- Final optical power test
Severity: 8
Occurrence: 5
Detection: 5
Recommended Actions:
- Run fixture GRR
- Track coupling shift by adhesive lot
Owner: Process Eng
Target Completion: 2026-06-10
Status: Open

## Row F2

Item / Function: Laser drive setup
Failure Mode: Incorrect drive current limit
Effects:
- Power instability
- Reliability stress
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
- Lock approved firmware in setup
- Add first-article current audit
Owner: Test Eng
Target Completion: 2026-06-05
Status: In Progress

## Row F3

Item / Function: Label printing
Failure Mode: Wrong label format
Effects:
- Rework before shipment
Causes:
- Wrong template selected
Prevention Controls:
- Released label template
Detection Controls:
- Final visual inspection
Severity: 3
Occurrence: 2
Detection: 4
Recommended Actions:
- Add template lock
Owner: QA
Target Completion: 2026-06-02
Status: Open
