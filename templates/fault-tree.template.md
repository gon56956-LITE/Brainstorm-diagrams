---
# Fault tree template for non-technical authors.
# Edit the values below, then edit the structured body after the second "---".
# Required: diagram_type must stay fault_tree.
# Recommended: keep show_legend true unless the diagram will be used in a very small space.
# Gate values: use only OR or AND. If unsure, use OR.
# OR means any child event can cause the parent event.
# AND means all child events must happen together to cause the parent event.
# Markdown structure:
#   #  = top event
#   ## = first-level intermediate event
#   ### = second-level intermediate event under the most recent ##
#   -  = basic event leaf under the current ## or ###
# Put direct basic-event bullets before any ### nested events in the same ## block.
# Current renderer supports top event, event detail, AND/OR gates,
# intermediate events, and basic event leaves. Do not add probability,
# Boolean formulas, or dynamic fault-tree syntax yet.
diagram_type: fault_tree
title: Fault Tree Analysis
subtitle: Top Event - System Fails to Start
show_legend: true
---

# System Fails to Start
Gate: OR

Event Detail:
- Observed during cold start after overnight storage
- Scope: engineering samples from batch A
- Impact: startup blocked until power cycle
- Review focus: identify which branch should be tested first

## Power Path Issue
Gate: OR
- No Input Power
- Power Module Fault

### Fuse Opens Under Startup Surge
Gate: AND
- Fuse Aging
- High Inrush Current

### Input Connector Intermittent
Gate: OR
- Connector Not Fully Seated
- Harness Pin Backed Out

## Control Unit Issue
Gate: AND
- Firmware Crash
- Controller Fault

## Start Signal Issue
Gate: OR
- Start Button Failure
- Signal Line Disconnected
- Sensor Fault
