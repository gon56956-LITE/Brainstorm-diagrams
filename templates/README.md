# Templates

These files are starting points for user-authored diagram inputs. Copy a template, edit the content, then render it with `scripts/generate_diagram.py`.

Templates are protected by structural checks in `scripts/verify_testcases.py`. They should remain parseable and include:

- fishbone: a topic, multiple categories, ordinary primary causes, at least one subcategory with child causes, and Markdown authoring guidance with current renderer limits
- fault_tree: a top event, event detail content, multiple first-level events, AND/OR gates, basic event leaves, and at least one nested intermediate-event example
- exclusion_tree: a target problem, 3-6 sequential checkpoints, pass/fail labels, fail conclusions, final pass conclusion, and Markdown authoring guidance with current renderer limits
- two_by_two_matrix: a preset-specific 2x2 matrix with 4-20 scored items, clear 1-5 X/Y score guidance, no hidden subtitle metadata, and no item-level notes that are not rendered
- roadmap_timeline: preset-specific swimlane roadmap or milestone timeline input with periods, phases, initiatives or milestones, decision points, summary/table content, and clear single-language guidance

Markdown templates keep user guidance in front matter comments so the parser ignores it. Keep the renderable body limited to headings, recognized key-value lines such as `Gate:` for fault tree, and bullets.

Do not store generated SVG outputs in this directory.
