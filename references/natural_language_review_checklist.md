# Natural Language Review Checklist

Use this checklist after Codex turns raw text into an editable Markdown draft. It checks semantic quality before or alongside visual review.

## Source Fidelity

- The diagram type matches the source intent: fishbone for broad brainstorming, fault tree for logical top-event decomposition, two-by-two matrix for two-axis option comparison, roadmap timeline for planning over time.
- Exclusion tree is used only for sequential troubleshooting, practical verification checks, or cause-elimination workflows.
- Roadmap timeline is used only when the source includes dates, periods, phases, milestones, or initiative timing.
- The topic or top event preserves the source's central problem, failure mode, design challenge, or analysis question.
- Labels come from the source domain, not from generic defaults unless the source explicitly asks for them.
- Causes, branches, and leaves are traceable to the source text.
- The draft does not add unsupported facts, measurements, root-cause conclusions, or corrective actions.
- Wording may be shortened or normalized, but meaning should not shift.

## Fishbone Structure

- The draft uses 4-8 categories.
- Each category has 2-5 primary entries when the source supports them.
- If the source asks for subcategories, each category stays within renderer limits: up to 5 primary entries, up to 3 child causes per subcategory.
- If the source does not ask for subcategories, default to category + primary causes only.
- Similar causes are grouped under sensible categories rather than duplicated across multiple categories.

## Fault Tree Structure

- The draft uses `diagram_type: fault_tree`.
- The top event is one specific undesired event, not a broad project title.
- `Event Detail:` captures observations, scope, conditions, impact, or review focus from the source.
- First-level intermediate events are logical cause branches.
- Basic event leaves are concrete enough to test or review.
- `Gate: OR` is used for independent possible causes.
- `Gate: AND` is used only when the source explicitly says conditions must occur together.
- Nested `###` intermediate events are used only when mixed logic or second-level decomposition is needed.
- The draft does not imply a proven root cause unless the source states it.

## Sequential Exclusion Tree Structure

- The draft uses `diagram_type: exclusion_tree`.
- The target problem is one specific issue to troubleshoot, not a broad project title.
- `Event Detail:` captures observations, scope, conditions, excluded facts, or review focus from the source.
- The draft uses 3-6 checkpoints.
- Each checkpoint is phrased as a testable Yes/No question.
- The checkpoint order follows the source order or a practical troubleshooting path from broad/easy checks toward narrower checks.
- Each checkpoint has a source-traceable `Fail Conclusion:`.
- `Fail Detail:` is used only for source-supported evidence or verification notes.
- The draft has one `Final Pass Conclusion:` for the all-checks-pass path.
- The draft does not use AND/OR gates or fault-tree intermediate events.
- The draft does not imply a proven root cause unless the source states that a failed check confirms it.

## Two-by-Two Matrix Structure

- The draft uses `diagram_type: two_by_two_matrix`.
- The preset or custom axis pair matches the source's comparison dimensions.
- The diagram is single-language unless the user explicitly requests bilingual content.
- The draft has 4-20 items; if the source has more than 20 options, it is split or summarized before rendering.
- Each item has a clear name and source-traceable `X` and `Y` scores from 1-5.
- The horizontal and vertical dimensions are not swapped.
- There is no `Subtitle:` or item-level `Notes` column unless explicitly requested.
- Top-level `notes:` is used only for a short visible note supported by the source, roughly 70 English characters or 30 Chinese characters.
- The draft does not imply exact quantitative precision when the source only supports ordinal ranking.

## Roadmap Timeline Structure

- The draft uses `diagram_type: roadmap_timeline`.
- The preset matches the source structure: `swimlane_roadmap` for multiple parallel tracks, `milestone_timeline` for one sequence of key events.
- The diagram is single-language unless the user explicitly requests bilingual content.
- The title and `Goal:` line preserve the source roadmap topic and planning objective.
- There is no `Subtitle:` unless explicitly requested.
- Dates, periods, phases, and marker timing are source-supported. Quarter/month-only source timing is converted conservatively and kept visible in labels.
- For `swimlane_roadmap`, the draft has at least two time periods, at least two lanes, source-specific initiative bars, and valid lane IDs.
- For `swimlane_roadmap`, milestones and decision points are used only for explicit launches, reviews, gates, approvals, or decisions.
- For `milestone_timeline`, the draft has multiple ordered milestones with type, owner/status/output when supported.
- For `milestone_timeline`, phases are date ranges and not duplicates of point milestones.
- Notes are short and review-relevant, not full recommendation paragraphs.

## File Outputs

- The editable draft is saved as `work/<diagram-type>/<safe-name>.md`.
- The rendered SVG is saved as `work/<diagram-type>/<safe-name>.svg`.
- PNG is exported only when useful, as `work/<diagram-type>/<safe-name>.png`.
- Raw `.txt` is not passed directly to `scripts/generate_diagram.py` for semantic extraction.

## Review Questions

- Would a domain reviewer recognize these labels as belonging to the source problem?
- Are any categories or branches just placeholders that should be replaced with source-specific wording?
- Are any causes, branches, or gate relationships too speculative for the provided text?
- Are important source phrases missing from the draft?
- For fishbone, does the resulting diagram invite useful brainstorming rather than imply a final proven root cause?
- For fault tree, does the diagram show logical failure decomposition without overstating proof?
- For sequential exclusion tree, would a technician know what to check next without mistaking suspected causes for confirmed root causes?
- For two-by-two matrix, would a reviewer agree that each option lands in a reasonable quadrant based on the source?
- For roadmap timeline, would a reviewer recognize the lanes, date ranges, gates, and phases as the source plan rather than an invented schedule?
