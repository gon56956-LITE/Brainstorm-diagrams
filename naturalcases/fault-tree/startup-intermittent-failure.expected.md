---
diagram_type: fault_tree
title: Fault Tree Analysis
subtitle: Top Event - Unit Fails to Complete Cold Startup
show_legend: true
---

# Unit Fails to Complete Cold Startup
Gate: OR

Event Detail:
- Intermittent failure after overnight low-temperature storage
- Clears after a full power cycle in most observed cases
- Seen on engineering samples from two assembly lots
- Review goal: break down possible logical causes, not prove a final root cause

## Input Power Path Instability
Gate: OR
- Input Voltage Droop During Inrush
- Intermittent Connector Seating
- Cold-Soak Sensitive Harness Contact

## Controller Boot Not Reached
Gate: OR
- Firmware Log Stops Before Ready Handshake
- Controller Does Not Enter Normal Boot Sequence

### Power-Good Timing Blocks Boot
Gate: AND
- Power-Good Signal Delayed
- Controller Boot Requires Stable Power-Good

## Start Signal Not Generated
Gate: AND
- Power-Good Line Not Stable
- Controller Does Not Exit Boot

## Cold Storage Sensitivity
Gate: OR
- Failure More Likely After Cold Soak
- Room-Temperature Storage Does Not Reproduce Consistently
