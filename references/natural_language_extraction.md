# Natural Language Extraction

Use this reference when a user asks Codex to create a diagram draft from raw customer feedback, workshop notes, failure notes, problem statements, or other unstructured text.

This is a Codex skill workflow. The local renderer does not infer semantic structure from plain `.txt` files by itself.

For a reusable execution prompt, use `references/natural_language_prompt_template.md`.

## Goal

Turn natural language into an editable structured Markdown draft, then render that Markdown through the existing SVG/PNG toolchain.

Choose `fishbone` when the source asks for broad cause brainstorming, category-based decomposition, or Ishikawa-style exploration:

```markdown
# Topic

## Domain-specific category
- Primary cause
- Primary cause
```

Choose `fault_tree` when the source asks for logical failure decomposition, FTA, top-event breakdown, AND/OR relationships, or causal logic:

```markdown
---
diagram_type: fault_tree
title: Fault Tree Analysis
show_legend: true
---

# Top Event
Gate: OR

Event Detail:
- Observed context
- Scope and impact

## Intermediate Event
Gate: OR
- Basic event
- Basic event
```

Choose `exclusion_tree` when the source asks for sequential troubleshooting, step-by-step cause elimination, verification checks, root-cause screening, or a practical diagnostic path:

```markdown
---
diagram_type: exclusion_tree
show_legend: true
show_how_to_use: true
---

# Target Problem

Event Detail: Observed context and review goal
- Supporting observation

## Checkable Condition OK?
Fail Conclusion: Likely Cause if Check Fails
Fail Detail: Source-supported evidence or next verification note

Final Pass Conclusion: No issue found in this path. Consider other causes or deeper analysis.
```

Choose `two_by_two_matrix` when the source asks to compare, rank, or prioritize options across two scoring dimensions:

```markdown
---
diagram_type: two_by_two_matrix
preset: action_priority
language: auto
show_side_table: true
show_legend: true
---

# Matrix Title

Subtitle: Compare options by impact and effort

## Items

| ID | Item | X | Y | Notes |
|---|---|---:|---:|---|
| A1 | Option name | 2 | 5 | Source-supported note |
```

## Extraction Rules

### Fishbone

- Extract 4-8 categories from the user's actual content.
- Prefer domain-specific category names over generic fishbone defaults.
- Do not use default categories such as People, Process, Tools, Materials, Environment, or Methods unless the user's source text clearly supports them.
- Put 2-5 primary causes under each category when the source text supports them.
- Default to category + primary cause depth only.
- Do not invent subcategories or second-level causes unless the user explicitly asks for them or the source text already has that structure.
- Preserve the user's meaning and vocabulary where possible. Lightly normalize wording for clarity, but do not add unsupported facts.
- If the source text is too thin to produce at least 4 meaningful categories, ask the user for more context instead of filling gaps with default categories.
- For product design, manufacturing, or application text, consider categories such as system architecture, optical design, thermal design, mechanical design, electrical design, materials, manufacturing, verification, field use, data center, cloud, communication, network, cost, or business only when the source supports them. Do not force this list.

### Fault Tree

- Extract one specific top event from the user's stated failure mode.
- Extract an `event_detail` panel from observed symptoms, scope, operating conditions, affected units, and review focus.
- Use first-level intermediate events for major logical cause branches, not generic fishbone categories.
- Use `OR` when any listed child event could independently cause the parent.
- Use `AND` only when the source states that conditions must occur together, such as "requires both", "only when X and Y", or "combination of".
- Do not infer AND logic from mere co-occurrence. If unsure, use `OR`.
- Use basic event leaves for concrete observable causes, test findings, missing conditions, or component/process faults.
- Use a nested `###` intermediate event when one branch needs a second gate to explain mixed logic.
- Preserve uncertainty. Do not present suspected causes as proven root causes unless the source states they are proven.
- Do not add probabilities, Boolean formulas, dynamic fault-tree syntax, mitigations, or corrective actions.
- Keep the draft within the current renderer scope: one top event, recommended 3-5 first-level intermediate events, up to eight first-level intermediate events when the source needs it, up to four children per intermediate event, and optional second-level intermediate events.
- If the source is too thin to support at least two meaningful cause branches, ask for more context instead of inventing branches.

### Sequential Exclusion Tree

- Extract one target problem from the source issue or investigation question.
- Extract an `Event Detail:` panel from observed symptoms, scope, operating conditions, affected units, excluded facts, and review goal.
- Extract 3-6 sequential checkpoints when the source supports at least three practical checks.
- Phrase every checkpoint as a testable Yes/No question, such as "Power Rail Within Tolerance?" or "Connector Dry and Sealed?"
- Order checkpoints by practical troubleshooting flow from broad, easy, or safety-critical checks toward narrower checks when the source implies an order; otherwise preserve the source order.
- Use each `Fail Conclusion:` for the likely cause or priority investigation result if that check fails.
- Use `Fail Detail:` for source-supported evidence, observed clues, or the verification note behind the conclusion.
- Use `Final Pass Conclusion:` for the result when all checks pass, usually to consider less common causes or deeper analysis.
- Do not use AND/OR gates, probability, Boolean logic, or fault-tree intermediate events in a sequential exclusion tree.
- Do not present suspected causes as proven root causes unless the source says a failed check has confirmed them.
- Keep the draft within the current renderer scope: one target problem, event detail, 3-6 checkpoints, one No/Fail conclusion per checkpoint, and one final pass conclusion.
- If the source is too thin to support a target problem and at least three meaningful check directions, ask for more context instead of generating a generic troubleshooting flow.

### Two-by-Two Matrix

- Extract the two comparison dimensions from the source.
- Choose the closest preset: `action_priority`, `risk_benefit`, `evidence_impact`, `value_feasibility`, or `urgency_importance`; use `custom` only when the source gives a different axis pair.
- Use `language: auto` unless the user explicitly requests `en` or `zh`.
- Keep diagram labels single-language. Do not render English/Chinese pairs by default.
- Extract each item or option as one row with `X` and `Y` scores from 1-5.
- Use `X` for the horizontal dimension and `Y` for the vertical dimension.
- Keep notes short and source-traceable.
- Do not invent precise quantitative scores when the source is vague; use conservative ordinal scoring from the described strength of each dimension.
- Do not model this as precise scatter/bubble placement. The current renderer uses scores to classify items into quadrant lists and a side summary table.

## Workflow

1. Read the user's natural-language source.
2. Choose `fishbone`, `fault_tree`, `exclusion_tree`, or `two_by_two_matrix` based on the source and the user's wording.
3. Extract the diagram structure using the rules above.
4. Write structured Markdown to `work/<diagram-type>/<safe-name>.md`.
5. Render the SVG with the matching work renderer or `scripts/generate_diagram.py`.
6. Export PNG only if the user wants a shareable image.
7. Review semantic quality with `references/natural_language_review_checklist.md`.
8. When the request is similar to an existing naturalcase, compare against `naturalcases/<diagram-type>/` examples for expected depth and specificity.

## Prompt Example

```text
根据下面客户反馈生成鱼骨图草稿，文件名 customer-complaints：

最近客户投诉集中在交付周期变长、包装破损、售后响应慢、现场安装说明不清楚、
不同供应批次质量波动，以及内部测试覆盖不到真实使用场景。
```

Expected behavior:

- Create `work/fishbone/customer-complaints.md`.
- Use categories derived from the feedback, such as delivery, packaging, service response, field installation, supplier quality, and test coverage.
- Render `work/fishbone/customer-complaints.svg`.
- Do not default to generic categories unless they fit the actual feedback.

## Fault Tree Prompt Example

```text
Create a fault tree diagram draft from the source text below.

Output name: startup-intermittent-failure

The unit sometimes fails to complete cold startup after overnight storage.
The failure appears only after low-temperature soak and clears after a full power cycle.
Observed units show input voltage droop during inrush on two samples, but not all samples.
Firmware logs sometimes stop before the ready handshake.
The start signal is generated only when the power-good line is stable and the controller exits boot.
Some harness checks found intermittent connector seating on one lot.
The review goal is to break down possible logical causes, not to prove one root cause yet.
```

Expected behavior:

- Create `work/fault-tree/startup-intermittent-failure.md`.
- Use the top event "Unit Fails to Complete Cold Startup" or equivalent.
- Use event detail for observed context, scope, and review goal.
- Use OR for independent branches such as power path, controller boot, and start signal path.
- Use AND only for explicitly combined conditions such as power-good stability plus controller boot completion.
- Render `work/fault-tree/startup-intermittent-failure.svg`.

## Sequential Exclusion Tree Prompt Example

```text
Create a sequential exclusion tree troubleshooting draft from the source text below.

Output name: field-link-dropout

The remote sensor link intermittently drops offline after installation at customer sites.
The outage usually appears after rain or washdown and sometimes clears after the cabinet is opened and reseated.
Two returned units had moisture marks near the outdoor connector.
Field logs show receive signal level below the normal threshold during several outages.
One site had a loose shield termination on the cable harness.
Bench replay with the same firmware did not reproduce the disconnect.
The power rail remained within tolerance during the captured outage window.
The goal is to guide technicians through checks that can exclude likely causes in a practical order.
```

Expected behavior:

- Create `work/exclusion-tree/field-link-dropout.md`.
- Use the target problem "Remote Sensor Link Drops Offline After Field Installation" or equivalent.
- Use event detail for observed context, excluded facts, and review goal.
- Use sequential checks such as connector sealing, receive signal threshold, shield termination, and firmware reproduction.
- Use No/Fail conclusions only for source-supported likely causes.
- Render `work/exclusion-tree/field-link-dropout.svg`.
