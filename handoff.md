# brainstorm-diagrams Handoff

Use this file to start a new Codex session with minimal context.

## Current State

Repository path:

```text
<skills-root>\brainstorm-diagrams
```

Remote repositories:

- Gitea: `ssh://git@10.89.7.78:2225/zan_gong/Brainstorm-diagrams.git`
- GitHub: `https://github.com/gon56956-LITE/Brainstorm-diagrams`

Current branch:

```text
main
```

The project currently implements one production diagram type:

```text
diagram_type = fishbone
```

Fishbone is implemented as deterministic SVG from structured Markdown or JSON, with optional PNG export. Natural-language fishbone drafting is a Codex workflow that first writes structured Markdown, then renders it.

## Important Current Structure

Diagram-specific files are now scoped by diagram type:

```text
testcases/
  fishbone/

stresscases/
  fishbone/

naturalcases/
  fishbone/

work/
  fishbone/
```

Templates are still flat because only fishbone is implemented:

```text
templates/
  fishbone.template.md
  fishbone.template.json
```

Renderers live under:

```text
scripts/renderers/
  fishbone.py
```

## Fishbone Capabilities Already Done

- Structured Markdown and JSON input.
- Subcategories with up to three child causes.
- Compact curly braces for subcategory child bullets.
- Alternating left/right primary entries and subcategories.
- Content-density branch lengths.
- Content-aware top/bottom category assignment.
- Footprint-aware horizontal placement.
- Automatic SVG canvas expansion for dense content.
- Topic block text wrapping.
- Lucide-based blue badge candidate library under `assets/lucide-candidates/`.
- Confirmed Lucide mappings for technical categories such as system, architecture, optical, thermal, mechanical, electrical, materials, manufacturing, reliability, field use, test, verification, cost, and business.
- PNG export compatible with current renderer SVGs and Lucide-style nested icon groups.
- Non-technical double-click launcher: `fishbone_tool.cmd` and `鱼骨图工具.cmd`.

## Key References

Read these first in a new session:

```text
SKILL.md
README.md
references/maintenance_checklist.md
brainstorm_diagrams_fault_tree_spec.md
```

Fishbone-specific references worth knowing:

```text
references/input_contract.md
references/layout_invariants.md
references/visual_style_contract.md
references/natural_language_extraction.md
references/natural_language_prompt_template.md
references/natural_language_review_checklist.md
references/visual_review_checklist.md
```

## Verification

Full verification set:

```powershell
python scripts\verify_testcases.py
python scripts\verify_stresscases.py
python scripts\verify_naturalcases.py
cmd /c fishbone_tool.cmd verify
```

## Recommended Next Work

Implement the second diagram type:

```text
diagram_type = fault_tree
```

Recommended first phase:

1. Read `brainstorm_diagrams_fault_tree_spec.md`.
2. Define fault-tree Markdown and JSON input shape.
3. Add `templates/fault-tree.template.md` and `templates/fault-tree.template.json`.
4. Add `scripts/renderers/fault_tree.py`.
5. Extend `scripts/generate_diagram.py` dispatch.
6. Add `testcases/fault-tree/`.
7. Add verification coverage without breaking existing fishbone tests.
8. Only after the renderer is stable, update the `.cmd` menu to choose diagram type.

Keep the first fault-tree implementation small:

- Top event.
- AND / OR gates.
- Basic event leaves.
- Deterministic SVG.
- Same business-simple visual language as fishbone.
- No probability math, no Boolean simplification, no dynamic fault tree.

## Suggested New Session Prompt

```text
继续开发 <skills-root>\brainstorm-diagrams。
请先阅读 handoff.md、SKILL.md、README.md、references/maintenance_checklist.md 和 brainstorm_diagrams_fault_tree_spec.md。
当前 fishbone 已完成并已按 diagram type 重组目录。
请开始实现第二种 diagram：fault_tree。先做最小可用版本：top event、AND/OR gate、basic event leaves、Markdown/JSON 输入、SVG renderer、templates、testcases 和验证。
```
