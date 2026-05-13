# Natural Language Review Checklist

Use this checklist after Codex turns raw text into a fishbone Markdown draft. It checks semantic quality before or alongside visual review.

## Source Fidelity

- The topic preserves the source's central problem, failure mode, design challenge, or analysis question.
- Category names come from the source domain, not from generic defaults unless the source explicitly asks for them.
- Causes are traceable to the source text.
- The draft does not add unsupported facts, measurements, root-cause conclusions, or corrective actions.
- Wording may be shortened or normalized, but meaning should not shift.

## Structure

- The draft uses 4-8 categories.
- Each category has 2-5 primary entries when the source supports them.
- If the source asks for subcategories, each category stays within renderer limits: up to 5 primary entries, up to 3 child causes per subcategory.
- If the source does not ask for subcategories, default to category + primary causes only.
- Similar causes are grouped under sensible categories rather than duplicated across multiple categories.

## File Outputs

- The editable fishbone draft is saved as `work/fishbone/<safe-name>.md`.
- The rendered SVG is saved as `work/fishbone/<safe-name>.svg`.
- PNG is exported only when useful, as `work/fishbone/<safe-name>.png`.
- Raw `.txt` is not passed directly to `scripts/generate_diagram.py` for semantic extraction.

## Review Questions

- Would a domain reviewer recognize these categories as belonging to the source problem?
- Are any categories just placeholders that should be replaced with source-specific wording?
- Are any causes too speculative for the provided text?
- Are important source phrases missing from the draft?
- Does the resulting diagram invite useful brainstorming rather than imply a final proven root cause?
