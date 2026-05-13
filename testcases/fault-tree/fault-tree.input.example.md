---
diagram_type: fault_tree
title: Fault Tree Analysis
subtitle: Top Event - System Fails to Start
show_legend: true
---

# System Fails to Start
Gate: OR

Event Detail:
- Observed during cold start after overnight storage
- Scope: units from batch A
- Impact: startup blocked until power cycle

## Power Issue
Gate: OR
- No Power Supply
- Power Module Fault
- Fuse Blown

## Control Unit Issue
Gate: AND
- Firmware Crash
- Controller Fault

## Start Signal Issue
Gate: OR
- Start Button Failure
- Signal Line Disconnected
- Sensor Fault
