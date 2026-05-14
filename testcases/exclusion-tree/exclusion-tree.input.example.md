---
diagram_type: exclusion_tree
title: Exclusion Tree / 排除树
subtitle: Sequential checks narrow the possible root cause.
show_legend: true
show_how_to_use: true
---

# System Fails to Start

Event Detail Title: Event Detail
Event Detail: The system does not complete startup after power is applied.
- Observed during validation after overnight storage
- Use the checks below in sequence

## Power Input OK?
Icon: bolt
Fail Conclusion: No Power Input
Fail Detail: Check power cable and outlet.

## Power Module Output OK?
Icon: module
Fail Conclusion: Power Module Fault

## Control Board OK?
Icon: chip
Fail Conclusion: Control Board Fault

## Start Signal OK?
Icon: signal
Fail Conclusion: Start Signal Issue

Final Pass Conclusion: No issue found in this path. Consider other rare causes or deeper analysis.
