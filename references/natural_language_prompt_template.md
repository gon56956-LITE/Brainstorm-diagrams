# Natural Language Prompt Template

Use this template when Codex turns raw customer text, workshop notes, product-design notes, manufacturing issues, field-application feedback, or failure-analysis notes into an editable Markdown draft.

This is a Codex workflow template. Do not pass raw `.txt` directly to `scripts/generate_diagram.py` for semantic extraction.

## Prompt Pattern

```text
Create a diagram draft from the source text below.

Output name: <safe-name>
Goal: create an editable Markdown draft and render SVG.

Diagram choice:
- Choose `fishbone` when the source asks for broad cause brainstorming, category-based decomposition, or Ishikawa-style exploration.
- Choose `fault_tree` when the source asks for logical failure decomposition, FTA, top-event breakdown, AND/OR relationships, or causal logic.
- Choose `exclusion_tree` when the source asks for sequential troubleshooting, step-by-step cause elimination, verification checks, or a practical diagnostic path.
- Choose `two_by_two_matrix` when the source asks to compare or prioritize options across two scoring dimensions, such as impact/effort, risk/benefit, evidence/impact, value/feasibility, or urgency/importance.
- Choose `roadmap_timeline` when the source asks for a roadmap, timeline, release plan, milestone plan, phase plan, launch schedule, or cross-team execution plan over time.

Rules:
- Read the source text first; do not start from default fishbone categories, generic fault-tree branches, or generic troubleshooting steps.
- Preserve source meaning and domain vocabulary. Lightly normalize names for clarity.
- Do not invent facts, test results, measurements, root-cause conclusions, or corrective actions.

Fishbone rules:
- Extract a concise topic from the source's central problem, design challenge, or analysis question.
- Extract 4-8 domain-specific categories from the source.
- Put 2-5 primary causes under each category when supported by the source.
- Default to category + primary cause depth only.
- Do not create subcategories or second-level causes unless the source already has a clear hierarchy or the user explicitly asks for them.
- If the source is too thin to support at least 4 meaningful categories, ask the user for more context instead of using default categories.

For product design / manufacturing / application text:
- Consider domain categories such as system architecture, optical design, thermal design, mechanical design, electrical design, materials, manufacturing, verification, field use, data center, cloud, communication, network, cost, or business only when the source supports them.
- Do not force every category from this list.

Fault-tree rules:
- Extract one specific top event from the source failure mode.
- Add an `Event Detail:` section for observed symptoms, scope, conditions, affected units, and review focus.
- Extract first-level intermediate events as major logical cause branches.
- Use `Gate: OR` when any child event could independently cause the parent.
- Use `Gate: AND` only when the source states that child conditions must occur together.
- Do not infer AND logic from mere co-occurrence. If unsure, use OR.
- Use `###` nested intermediate events only when a branch needs mixed logic or a second gate.
- Use bullets as concrete basic event leaves.
- Do not add probability, Boolean simplification, dynamic fault-tree syntax, mitigations, or corrective actions.
- If the source is too thin to support at least two meaningful fault branches, ask for more context instead of inventing branches.

Exclusion-tree rules:
- Extract one target problem from the source issue or investigation question.
- Add an `Event Detail:` section for observed symptoms, scope, conditions, excluded facts, and review goal.
- Extract 3-6 sequential checkpoints when the source supports at least three practical checks.
- Phrase each checkpoint as a testable Yes/No question.
- Order checks by practical troubleshooting flow when the source implies one; otherwise preserve source order.
- Use `Fail Conclusion:` for the likely cause or priority investigation result if that check fails.
- Use `Fail Detail:` only for source-supported evidence or verification notes.
- Add `Final Pass Conclusion:` for the result when all checks pass.
- Do not use AND/OR gates, probability, Boolean logic, or fault-tree intermediate events.
- If the source is too thin to support a target problem and at least three meaningful check directions, ask for more context instead of generating a generic troubleshooting flow.

Two-by-two matrix rules:
- Choose the closest preset: `action_priority`, `risk_benefit`, `evidence_impact`, `value_feasibility`, or `urgency_importance`; use `custom` only when the source gives its own axis names.
- Keep the diagram single-language. Use `language: auto` unless the user explicitly requests `en` or `zh`; do not create English/Chinese paired labels by default.
- Extract items/options from the source and score each item on both axes from 1-5 using only source-supported wording.
- Use the horizontal score as `X` and the vertical score as `Y`.
- Include 4-20 scored items. If the source has more than 20 options, ask the user to split the matrix or summarize before rendering.
- Do not add `Subtitle:` unless the user explicitly asks for a subtitle.
- Do not add an item-level `Notes` column. Use top-level `notes:` only when the user asks for a visible note or the source includes a short note that should appear on the diagram.
- Keep top-level `notes:` short enough for a two-line guide card: roughly 70 English characters or 30 Chinese characters. Use a decision-summary phrase, not a full recommendation paragraph.
- Do not turn the matrix into a precise scatter plot; items are grouped into quadrant lists.

Roadmap timeline rules:
- Choose `preset: swimlane_roadmap` when the source contains multiple lanes such as products, models, modules, workstreams, teams, regions, themes, or customer segments.
- Choose `preset: milestone_timeline` when the source mainly gives one sequence of key dates, gates, deliverables, or phases.
- Keep the diagram single-language. Use `language: auto` unless the user explicitly requests `en` or `zh`; do not create English/Chinese paired labels by default.
- Extract a visible title and `Goal:` line from the source's roadmap topic and planning objective.
- Do not add `Subtitle:` unless the user explicitly asks for a subtitle.
- For swimlane roadmaps, extract time periods, lanes, initiatives, milestones, decision points, and short notes when supported.
- For milestone timelines, extract milestones, phases, owner/status/output details, and short notes when supported.
- Use explicit dates from the source. If the source gives only quarters or months, convert them to reasonable period start/end dates and preserve the visible label.
- Use marker types from `start`, `milestone`, `key_milestone`, `decision`, `review`, and `launch`; use statuses from `planned`, `in_progress`, `completed`, and `at_risk`.
- Keep labels short enough for diagram cards and bars; put longer explanations in milestone `Output` or a short note.
- If the source lacks dates or a clear sequence, ask for date ranges or milestone timing instead of inventing a schedule.

Execution:
1. Write structured Markdown to `work/<diagram-type>/<safe-name>.md`.
2. Render SVG with the matching work renderer or `scripts/generate_diagram.py`.
3. Export PNG only if the user requests it.
4. Review with `references/natural_language_review_checklist.md`.

Source text:
<paste source text here>
```

## Fishbone Markdown Output Shape

```markdown
# Topic

## Domain-specific Category
- Primary cause
- Primary cause

## Domain-specific Category
- Primary cause
- Primary cause
```

## Fault Tree Markdown Output Shape

```markdown
---
diagram_type: fault_tree
title: Fault Tree Analysis
show_legend: true
---

# Top Event
Gate: OR

Event Detail:
- Observation
- Scope
- Review focus

## Intermediate Event
Gate: OR
- Basic event
- Basic event

## Intermediate Event Requiring Combined Conditions
Gate: AND
- Required condition
- Required condition
```

## Sequential Exclusion Tree Markdown Output Shape

```markdown
---
diagram_type: exclusion_tree
title: Sequential Exclusion Tree
show_legend: true
show_how_to_use: true
---

# Target Problem

Event Detail Title: Event Detail
Event Detail: Observed context and review goal
- Supporting observation

## Checkable Condition OK?
Fail Conclusion: Likely Cause if Check Fails
Fail Detail: Source-supported evidence or next verification note

## Next Checkable Condition OK?
Fail Conclusion: Next Likely Cause if Check Fails

Final Pass Conclusion: No issue found in this path. Consider other causes or deeper analysis.
```

## Two-by-Two Matrix Markdown Output Shape

```markdown
---
diagram_type: two_by_two_matrix
preset: action_priority
language: auto
show_side_table: true
show_legend: true
---

# Matrix Title

notes: Optional visible note supported by the source

## Items

| ID | Item | X | Y |
|---|---|---:|---:|
| A1 | Option name | 2 | 5 |
| A2 | Option name | 5 | 4 |
```

## Roadmap Timeline Markdown Output Shape

Swimlane roadmap:

```markdown
---
diagram_type: roadmap_timeline
preset: swimlane_roadmap
lane_type: workstream
language: auto
time_granularity: quarter
show_table: true
show_summary_panel: true
---

# Roadmap Title

**Goal:** Visible roadmap goal from the source.

## Time Periods

| ID | Label | Subtitle | Start | End |
|---|---|---|---|---|
| 2026Q1 | 2026 Q1 | Jan - Mar | 2026-01-01 | 2026-03-31 |

## Lanes

| ID | Name | Color |
|---|---|---|
| hardware | Hardware | blue |

## Initiatives

| ID | Lane ID | Name | Start | End | Owner | Status |
|---|---|---|---|---|---|---|
| R1 | hardware | Prototype build | 2026-01-15 | 2026-03-15 | Hardware | planned |

## Milestones

| ID | Lane ID | Name | Date | Type |
|---|---|---|---|---|
| M1 | hardware | Architecture review | 2026-03-15 | review |

## Decision Points

| ID | Lane ID | Name | Date | Type |
|---|---|---|---|---|
| D1 | hardware | Design freeze | 2026-08-15 | decision |
```

Milestone timeline:

```markdown
---
diagram_type: roadmap_timeline
preset: milestone_timeline
language: auto
time_granularity: month
show_detail_cards: true
show_table: true
---

# Milestone Timeline Title

**Goal:** Visible timeline goal from the source.

## Milestones

| ID | Name | Date | Type | Owner | Status | Output |
|---|---|---|---|---|---|---|
| T1 | Kickoff | 2026-01-10 | start | PMO | planned | Confirm scope and owners |

## Phases

| Name | Start | End |
|---|---|---|
| Planning | 2026-01-01 | 2026-02-28 |
```

## Quality Gate Before Rendering

- The chosen diagram type matches the user's intent.
- Fishbone topic is specific and not just a document title.
- Fishbone categories are source-specific, not generic defaults unless explicitly supported.
- Fishbone primary causes are traceable to source wording or a conservative summary of source meaning.
- Fault-tree top event is a specific undesired event.
- Fault-tree intermediate events describe logical cause branches, not vague categories.
- Fault-tree AND gates are justified by explicit source wording.
- Fault-tree basic event leaves are concrete and source-traceable.
- Exclusion-tree target problem is a specific issue to troubleshoot.
- Exclusion-tree checkpoints are testable Yes/No questions and source-traceable.
- Exclusion-tree fail conclusions do not overstate suspected causes as proven.
- Exclusion-tree draft has 3-6 checkpoints and a final pass conclusion.
- Two-by-two matrix preset and axes match the source comparison dimensions.
- Two-by-two matrix uses one language only unless the user explicitly provides or requests bilingual labels.
- Two-by-two matrix includes 4-20 items and does not use a subtitle or item-level notes unless explicitly requested.
- Two-by-two matrix items have source-traceable 1-5 scores on both axes.
- Roadmap timeline preset matches the source structure: swimlane for parallel lanes, milestone timeline for one sequence.
- Roadmap timeline uses one language only unless the user explicitly provides or requests bilingual labels.
- Roadmap timeline includes a visible goal, source-supported dates, and no subtitle unless explicitly requested.
- Swimlane roadmap initiatives are assigned to valid lane IDs and time periods cover all bars and markers.
- Milestone timeline milestones are ordered by date and phases are date ranges, not point events.
- Similar causes are grouped rather than duplicated.
- The draft stays within renderer limits for the selected diagram type.
- The file name is a safe stem: lowercase letters, numbers, hyphen, or underscore.
