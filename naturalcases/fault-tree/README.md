# Fault Tree Naturalcases

This folder contains natural-language source examples and expected structured Markdown drafts for Codex-assisted fault-tree drafting.

Naturalcases are examples for semantic extraction quality. They are not renderer regression outputs and should not contain generated SVG or PNG files.

Use them with:

- `references/natural_language_extraction.md`
- `references/natural_language_review_checklist.md`

Current cases:

- `startup-intermittent-failure.source.txt` -> `startup-intermittent-failure.expected.md`

Expected Markdown should use `diagram_type: fault_tree`, one top event, an event detail section, AND/OR gates, intermediate events, and basic event leaves. It should preserve uncertainty from the source and avoid adding probabilities, proven root-cause claims, Boolean simplification, or corrective actions.
