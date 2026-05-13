# Input Contract

All input sources should normalize into the same fishbone data model before rendering.

## Fishbone Model

```json
{
  "diagram_type": "fishbone",
  "title": "Structured Brainstorming",
  "topic": "Improve Product Reliability",
  "output": "svg",
  "theme": "business_simple",
  "categories": [
    {
      "name_en": "People",
      "items": [
        "Role clarity",
        {
          "subcategory": "Training",
          "items": ["Onboarding", "Skill matrix", "Certification"]
        }
      ]
    }
  ]
}
```

## Required Minimum

```json
{
  "diagram_type": "fishbone",
  "topic": "Problem or design challenge"
}
```

## Defaults

- `diagram_type`: `fishbone`
- `output`: `svg`
- `theme`: `business_simple`
- missing `topic`: `Problem / Topic`
- missing `categories`: renderer fallback uses default business categories for structured inputs only

## Language Policy

The renderer does not create bilingual labels. It outputs the text supplied by the input:

- English input produces English labels.
- Chinese input produces Chinese labels.
- If a user wants bilingual text, put the bilingual wording directly in the same field.
- Legacy fields such as `name_zh` and `topic_zh` may be accepted for compatibility, but they are not rendered as automatic secondary lines.

## Limits

- Category count is normalized to 4-8.
- Each category can contain up to 5 primary entries.
- A primary entry can be a cause string or a subcategory object.
- Each subcategory can contain up to 3 child cause items.
- The renderer outputs SVG. PNG is available as a post-render export from generated work SVGs via `scripts/export_png.py`.

## Natural-Language Source Text

Natural-language extraction is a Codex skill workflow, not part of the local renderer input model.

- Codex should extract `topic`, domain-specific `categories`, and primary `items` from the user's source text first.
- The extracted structure should be written as Markdown or JSON using this contract.
- Do not pass raw `.txt` to `scripts/generate_diagram.py` expecting semantic category extraction.
- Default categories should not be used for natural-language drafts unless the source text genuinely supports them.

See `references/natural_language_extraction.md`.

## Markdown Mapping

- First `#` heading becomes `topic`.
- Each `##` heading becomes a category.
- Bullet items under a category become primary entries.
- An indented bullet under a primary item turns that primary item into a subcategory.
- If no categories are found in structured Markdown, the renderer uses default categories as a fallback. Codex natural-language drafting should avoid this fallback by extracting meaningful categories first.

```markdown
# Customer Field Failures

## People
- Training
  - Onboarding
  - Skill matrix
  - Certification
- Role clarity
```

## Diagnostics

The CLI prints diagnostics after generation. Diagnostics are warnings only unless the requested diagram type or output format is unsupported.

## Subcategory Layout

Subcategories are a visual layout feature, not a separate diagram type. They render as text-only cards connected horizontally from an anchor on the main branch, with child causes shown as curly-braced bullets outside the card.
