# Implementation Checklist

## Phase 1 Acceptance

- [ ] `SKILL.md` exists and uses `name: brainstorm-diagrams`.
- [ ] JSON input can generate a valid SVG.
- [ ] Structured Markdown input can generate a valid SVG.
- [ ] Unsupported `diagram_type` returns a clear version 1 limitation message.
- [ ] Missing categories use defaults.
- [ ] Category count is normalized to 4-8.
- [ ] Each category is limited to 5 primary entries.
- [ ] Subcategories are limited to 3 child causes.
- [ ] Diagnostics are printed for defaults, truncation, ignored markdown levels, and compatibility fields.
- [ ] Mixed normal causes and subcategories can render in the same category.
- [ ] Topic block is a rounded rectangle.
- [ ] SVG is well-formed XML.
- [ ] Output avoids fish, marine, organic, and triangle topic-block elements.
