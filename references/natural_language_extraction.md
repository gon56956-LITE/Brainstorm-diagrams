# Natural Language Extraction

Use this reference when a user asks Codex to create a fishbone diagram from raw customer feedback, workshop notes, problem statements, or other unstructured text.

This is a Codex skill workflow. The local renderer does not infer fishbone structure from plain `.txt` files by itself.

For a reusable execution prompt, use `references/natural_language_prompt_template.md`.

## Goal

Turn natural language into an editable structured Markdown fishbone draft:

```markdown
# Topic

## Domain-specific category
- Primary cause
- Primary cause
```

Then render that Markdown through the existing SVG/PNG toolchain.

## Extraction Rules

- Extract 4-8 categories from the user's actual content.
- Prefer domain-specific category names over generic fishbone defaults.
- Do not use default categories such as People, Process, Tools, Materials, Environment, or Methods unless the user's source text clearly supports them.
- Put 2-5 primary causes under each category when the source text supports them.
- Default to category + primary cause depth only.
- Do not invent subcategories or second-level causes unless the user explicitly asks for them or the source text already has that structure.
- Preserve the user's meaning and vocabulary where possible. Lightly normalize wording for clarity, but do not add unsupported facts.
- If the source text is too thin to produce at least 4 meaningful categories, ask the user for more context instead of filling gaps with default categories.
- For product design, manufacturing, or application text, consider categories such as system architecture, optical design, thermal design, mechanical design, electrical design, materials, manufacturing, verification, field use, data center, cloud, communication, network, cost, or business only when the source supports them. Do not force this list.

## Workflow

1. Read the user's natural-language source.
2. Identify the central topic or problem statement.
3. Extract domain-specific categories and primary causes.
4. Write structured Markdown to `work/<safe-name>.md`.
5. Render the SVG with `scripts/render_work.py <safe-name>` or `scripts/generate_diagram.py`.
6. Export PNG with `scripts/export_png.py <safe-name>` only if the user wants a shareable image.
7. Review semantic quality with `references/natural_language_review_checklist.md`.
8. When the request is similar to an existing naturalcase, compare against `naturalcases/` examples for expected depth and category specificity.

## Prompt Example

```text
根据下面客户反馈生成鱼骨图草稿，文件名 customer-complaints：

最近客户投诉集中在交付周期变长、包装破损、售后响应慢、现场安装说明不清楚、
不同供应批次质量波动，以及内部测试覆盖不到真实使用场景。
```

Expected behavior:

- Create `work/customer-complaints.md`.
- Use categories derived from the feedback, such as delivery, packaging, service response, field installation, supplier quality, and test coverage.
- Render `work/customer-complaints.svg`.
- Do not default to generic categories unless they fit the actual feedback.
