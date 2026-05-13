# Templates

These files are starting points for user-authored diagram inputs. Copy a template, edit the content, then render it with `scripts/generate_diagram.py`.

Templates are protected by structural checks in `scripts/verify_testcases.py`. They should remain parseable and include:

- fishbone: a topic, multiple categories, ordinary primary causes, and at least one subcategory with child causes
- fault_tree: a top event, event detail content, multiple first-level events, AND/OR gates, basic event leaves, and at least one nested intermediate-event example

Fault tree templates intentionally include more guidance than fishbone templates because gate placement and nested-event structure are easier to misread. For Markdown, keep guidance in front matter comments and keep the body limited to headings, `Gate:` lines, `Event Detail:`, and bullets.

Do not store generated SVG outputs in this directory.
