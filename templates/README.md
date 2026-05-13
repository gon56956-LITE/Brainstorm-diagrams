# Templates

These files are starting points for user-authored fishbone inputs. Copy a template, edit the content, then render it with `scripts/generate_diagram.py`.

Templates are protected by structural checks in `scripts/verify_testcases.py`. They should remain parseable and include:

- a topic
- multiple categories
- ordinary primary causes
- at least one subcategory with child causes

Do not store generated SVG outputs in this directory.
