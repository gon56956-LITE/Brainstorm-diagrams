# Natural Language Prompt Template

Use this template when Codex turns raw customer text, workshop notes, product-design notes, manufacturing issues, or field-application feedback into a fishbone Markdown draft.

This is a Codex workflow template. Do not pass raw `.txt` directly to `scripts/generate_diagram.py` for semantic extraction.

## Prompt Pattern

```text
Create a fishbone diagram draft from the source text below.

Output name: <safe-name>
Goal: create an editable Markdown draft and render SVG.

Rules:
- Read the source text first; do not start from default fishbone categories.
- Extract a concise topic from the source's central problem, design challenge, or analysis question.
- Extract 4-8 domain-specific categories from the source.
- Put 2-5 primary causes under each category when supported by the source.
- Default to category + primary cause depth only.
- Do not create subcategories or second-level causes unless the source already has a clear hierarchy or the user explicitly asks for them.
- Preserve source meaning and domain vocabulary. Lightly normalize names for clarity.
- Do not invent facts, test results, measurements, root-cause conclusions, or corrective actions.
- If the source is too thin to support at least 4 meaningful categories, ask the user for more context instead of using default categories.

For product design / manufacturing / application text:
- Consider domain categories such as system architecture, optical design, thermal design, mechanical design, electrical design, materials, manufacturing, verification, field use, data center, cloud, communication, network, cost, or business only when the source supports them.
- Do not force every category from this list.

Execution:
1. Write structured Markdown to `work/<safe-name>.md`.
2. Render SVG with `scripts/render_work.py <safe-name>`.
3. Export PNG only if the user requests it.
4. Review with `references/natural_language_review_checklist.md`.

Source text:
<paste source text here>
```

## Markdown Output Shape

```markdown
# Topic

## Domain-specific Category
- Primary cause
- Primary cause

## Domain-specific Category
- Primary cause
- Primary cause
```

## Quality Gate Before Rendering

- Topic is specific and not just a document title.
- Categories are source-specific, not generic defaults unless explicitly supported.
- Each primary cause is traceable to source wording or a conservative summary of source meaning.
- Similar causes are grouped rather than duplicated.
- The draft stays within renderer limits: 4-8 categories and up to 5 primary entries per category.
- The file name is a safe stem for `work/`: lowercase letters, numbers, hyphen, or underscore.
