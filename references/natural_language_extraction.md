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

## Workflow

1. Read the user's natural-language source.
2. Choose `fishbone` or `fault_tree` based on the source and the user's wording.
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
