# Templates

These files are starting points for user-authored diagram inputs. Copy a template, edit the content, then render it with `scripts/generate_diagram.py`.

Templates are protected by structural checks in `scripts/verify_testcases.py`. They should remain parseable and include:

- fishbone: a topic, multiple categories, ordinary primary causes, at least one subcategory with child causes, and Markdown authoring guidance with current renderer limits
- fault_tree: a top event, event detail content, multiple first-level events, AND/OR gates, basic event leaves, and at least one nested intermediate-event example

Markdown templates keep user guidance in front matter comments so the parser ignores it. Keep the renderable body limited to headings, recognized key-value lines such as `Gate:` for fault tree, and bullets.

Do not store generated SVG outputs in this directory.
