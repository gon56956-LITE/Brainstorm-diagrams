---
diagram_type: exclusion_tree
show_legend: true
show_how_to_use: true
---

<!--
Exclusion trees are for sequential troubleshooting: check one condition, exclude one unlikely path, and stop when a failed check identifies a likely root cause.

Recommended limits:
- Top Event / Target Problem: 1
- Check Points: 3-6
- Each Check Point: one Yes/Pass continuation path and one No/Fail cause card
- Text guidance: write each checkpoint as a Yes/No question; keep cause cards short and add detail only when needed

How to write:
- # is the target problem / top event.
- Event Detail is the upper-left description panel. It may be one paragraph plus bullets.
- ## is a check point.
- Checkpoint icons are selected automatically from the question text.
- Pass is fixed as "Yes".
- Fail is fixed as "No".
- Fail Conclusion is the cause or priority investigation result shown on the No/Fail branch.
- Fail Detail is optional supporting detail inside the cause card.
- Final Pass Conclusion is the green result card when all checks pass.
-->

# System Fails to Start

Event Detail Title: Event Detail
Event Detail: The system does not complete startup after power is applied.
- Observed during validation after overnight storage
- Use the checks below in sequence
- Stop when a failed check identifies a likely root cause

## Power Input OK?
Fail Conclusion: No Power Input
Fail Detail: Check power cord, connector, and outlet.

## Power Module Output OK?
Fail Conclusion: Power Module Fault

## Control Board OK?
Fail Conclusion: Control Board Fault

## Start Signal OK?
Fail Conclusion: Start Signal Issue

Final Pass Conclusion: No issue found in this path. Consider other rare causes or deeper analysis.
