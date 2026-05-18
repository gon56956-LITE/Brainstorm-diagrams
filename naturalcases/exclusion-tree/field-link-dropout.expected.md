---
diagram_type: exclusion_tree
title: Sequential Exclusion Tree
show_legend: true
show_how_to_use: true
---

# Remote Sensor Link Drops Offline After Field Installation

Event Detail Title: Event Detail
Event Detail: Intermittent customer-site link outage that appears after rain or washdown and may clear after cabinet access or connector reseating.
- Same firmware build works on the lab bench
- Power rail stayed within tolerance during the captured outage window
- Review goal: guide technicians through practical checks without treating suspected causes as proven

## Outdoor Connector Dry and Sealed?
Fail Conclusion: Moisture Ingress at Outdoor Connector
Fail Detail: Returned units had moisture marks near the outdoor connector.

## Receive Signal Level Within Normal Threshold?
Fail Conclusion: Low Receive Signal During Outage
Fail Detail: Field logs showed receive signal level below the normal threshold during several outages.

## Cable Shield Termination Secure?
Fail Conclusion: Loose Shield Termination or Harness Seating Issue
Fail Detail: One site had a loose shield termination, and some outages cleared after reseating.

## Firmware Reproduces on Bench Replay?
Fail Conclusion: Firmware or Configuration-Specific Disconnect
Fail Detail: Bench replay with the same firmware did not reproduce the disconnect, so this check should confirm before assigning software cause.

Final Pass Conclusion: No issue found in this exclusion path. Consider less common site-specific causes or deeper field instrumentation.
