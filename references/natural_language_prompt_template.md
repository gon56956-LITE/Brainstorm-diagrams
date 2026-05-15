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

Rules:
- Read the source text first; do not start from default fishbone categories or generic fault-tree branches.
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

## Quality Gate Before Rendering

- The chosen diagram type matches the user's intent.
- Fishbone topic is specific and not just a document title.
- Fishbone categories are source-specific, not generic defaults unless explicitly supported.
- Fishbone primary causes are traceable to source wording or a conservative summary of source meaning.
- Fault-tree top event is a specific undesired event.
- Fault-tree intermediate events describe logical cause branches, not vague categories.
- Fault-tree AND gates are justified by explicit source wording.
- Fault-tree basic event leaves are concrete and source-traceable.
- Similar causes are grouped rather than duplicated.
- The draft stays within renderer limits for the selected diagram type.
- The file name is a safe stem: lowercase letters, numbers, hyphen, or underscore.
