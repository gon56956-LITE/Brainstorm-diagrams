# brainstorm-diagrams Skill Extension Spec: `fault_tree`

## 1. Purpose

This file defines a future extension for the `brainstorm-diagrams` Codex skill.

The `brainstorm-diagrams` skill is intended to generate PPT-ready structured thinking diagrams for brainstorming, product design, process design, failure analysis, troubleshooting, and root-cause analysis.

The first implemented diagram type is:

```text
diagram_type = fishbone
```

This document specifies the second recommended diagram type:

```text
diagram_type = fault_tree
```

The `fault_tree` diagram type should share the same visual language as the existing business-simple fishbone template: clean, professional, white-background, navy/light-blue corporate styling, and suitable for PowerPoint executive or engineering review.

---

## 2. Relationship to Existing Fishbone Template

The `fault_tree` template should visually feel like part of the same design family as the existing `fishbone` template.

Shared style principles:

- White or very light gray background.
- Navy blue as the primary color.
- Light blue and gray as secondary colors.
- Rounded rectangles for major event boxes.
- Thin connector lines.
- Small circular or semicircular nodes where needed.
- Simple line icons only.
- Clean sans-serif typography.
- Bilingual labels supported.
- Minimal decoration: subtle dots, faint circuit lines, or light geometric accents only.
- No realistic illustration style.
- No 3D, cartoon, glossy, decorative, or overly playful styling.

The fishbone template is used for divergent cause brainstorming.

The fault tree template is used for logical failure decomposition.

Recommended positioning inside the skill:

```text
fishbone = divergent cause brainstorming
fault_tree = logical failure decomposition
exclusion_tree = verification and elimination workflow
cause_screening_matrix = scoring and prioritization
```

---

## 3. When to Use `fault_tree`

Use the `fault_tree` diagram type when the user asks for:

- fault tree
- FTA
- fault tree analysis
- failure tree
- failure logic tree
- top event decomposition
- logical failure analysis
- root cause logic model
- system failure breakdown
- cause logic diagram
- AND/OR cause decomposition

Typical use cases:

- Failure analysis.
- Engineering troubleshooting.
- Product reliability review.
- System risk analysis.
- Design review.
- Process failure analysis.
- Customer issue analysis.
- Technical problem decomposition.

Do not use `fault_tree` for simple brainstorming where the user only wants a broad, category-based list of possible causes. Use `fishbone` for that.

---

## 4. Conceptual Definition

A fault tree diagram starts from a top-level undesirable event and decomposes it into lower-level causes.

The logic is top-down:

```text
Top Event
  = Intermediate Event A OR Intermediate Event B OR Intermediate Event C
```

Each intermediate event may be further decomposed:

```text
Intermediate Event A
  = Basic Event A1 OR Basic Event A2
```

Fault tree diagrams can express causal logic that fishbone diagrams usually do not express:

- OR relationship: any one cause can trigger the parent event.
- AND relationship: multiple causes must occur together to trigger the parent event.

The diagram should make these logical relationships visually clear.

---

## 5. Default Visual Layout

Default canvas:

```text
width: 1920 px
height: 1080 px
aspect ratio: 16:9
background: #FFFFFF or #F7FAFD
```

Default structure:

```text
Title area, upper left
Legend area, upper right
Top Event box, upper center
Gate under Top Event
Intermediate Event boxes in row 2
Gate under each intermediate event if it has children
Basic Event boxes or circles in lower rows
Optional notes / usage guide, lower right
```

Recommended hierarchy:

```text
Top Event
  ├─ Gate
  ├─ Intermediate Event 1
  │   ├─ Gate
  │   ├─ Basic Event 1.1
  │   ├─ Basic Event 1.2
  │   └─ Basic Event 1.3
  ├─ Intermediate Event 2
  │   ├─ Gate
  │   ├─ Basic Event 2.1
  │   ├─ Basic Event 2.2
  │   └─ Basic Event 2.3
  └─ Intermediate Event 3
      ├─ Gate
      ├─ Basic Event 3.1
      ├─ Basic Event 3.2
      └─ Basic Event 3.3
```

Default direction:

```text
top to bottom
```

---

## 6. Shape Language

Use only simple corporate vector shapes.

Allowed shapes:

- Rounded rectangles.
- Circles.
- Semicircle gate symbols.
- Simple line icons.
- Straight connector lines.
- Thin orthogonal connector paths.
- Subtle dotted grids.
- Faint circuit-line decorations.

Avoid:

- Realistic objects.
- Organic blobs.
- Cartoon illustrations.
- Heavy shadows.
- 3D effects.
- Gradient-heavy backgrounds.
- Decorative clip art.
- Complex icon illustrations.

---

## 7. Fault Tree Element Styles

### 7.1 Title

Recommended title format:

```text
Fault Tree Analysis / 故障树分析
```

Style:

```text
font: Arial, Helvetica, Microsoft YaHei, sans-serif
font size: 42 px
font weight: 700
fill: #0B2E63
position: x=60, y=72
```

Optional subtitle:

```text
Example: Top Event - System Fails to Start
示例：顶层事件 - 系统无法启动
```

Style:

```text
font size: 24-28 px
fill: #5B6B80
```

---

### 7.2 Top Event Box

The Top Event is the highest-level failure or undesirable outcome.

Recommended geometry:

```text
x: centered around canvas middle
y: 140
width: 310
height: 110
rx: 12-16
```

Recommended style:

```text
fill: #0B2E63 or #0B3A75
stroke: none or #0B2E63
text fill: #FFFFFF
```

Content:

```text
Top Event
系统无法启动
```

Optional icon:

- Warning triangle icon.
- Alert icon.
- Use white icon on navy background.

Icon should be simple and monochrome.

---

### 7.3 Intermediate Event Boxes

Intermediate events represent major cause groups or sub-failures.

Recommended style:

```text
fill: #F3F8FF
stroke: #2F6FB6
stroke width: 2
rx: 10-14
text fill: #0B2E63
```

Recommended content:

```text
1. Power Issue
电源问题
```

Layout:

- Usually placed in a horizontal row under the top gate.
- Three intermediate events are a good default.
- Support 2-5 intermediate events in the first implementation.

Optional icons:

- Power / battery icon.
- Gear icon.
- Signal icon.
- Sensor icon.
- Material / box icon.
- Process / flow icon.

Icons must be simple line icons.

---

### 7.4 Basic Event Boxes or Circles

Basic events are the lowest-level actionable or verifiable causes.

Recommended default shape:

```text
rounded rectangle
```

Alternative allowed shape:

```text
circle
```

Use circles when emphasizing that these are leaf-level basic events.

Recommended rounded rectangle style:

```text
fill: #FFFFFF or #F8FBFF
stroke: #7AAAE8
stroke width: 1.5
rx: 10
text fill: #0B2E63
```

Recommended circle style:

```text
fill: #F8FBFF
stroke: #7AAAE8
stroke width: 1.5
```

Content example:

```text
1.1 No Power Supply
无电源输入
```

---

### 7.5 OR Gate

OR Gate means any child event can cause the parent event.

Recommended visual:

- Dark navy semicircle / curved gate symbol.
- Simple, compact, clearly different from AND gate.

Recommended style:

```text
fill: #0B2E63
stroke: none
```

The exact gate shape may be simplified for PPT readability.

Suggested label behavior:

- Do not label every gate if it creates clutter.
- Use a legend to explain gate shapes.
- Optionally show small `OR` text near the symbol when the tree is small.

---

### 7.6 AND Gate

AND Gate means all child events must occur together to cause the parent event.

Recommended visual:

- Light blue semicircle / gate symbol.
- Distinct from OR gate by color and/or shape.

Recommended style:

```text
fill: #7AAAE8
stroke: none
```

Suggested label behavior:

- Use legend to explain.
- Optionally show `AND` text near the symbol.

---

### 7.7 Connectors

Connector style:

```text
stroke: #0B2E63 or #2F6FB6
stroke width: 2
fill: none
linecap: round
linejoin: round
```

Use clean orthogonal connectors:

```text
vertical line from parent to gate
horizontal bus line from gate to children
vertical line from bus to each child
```

Avoid diagonal spaghetti lines.

Connectors should align precisely.

---

### 7.8 Legend

Include a compact legend on the upper right by default.

Legend box style:

```text
fill: #FFFFFF
stroke: #9AA9BD
stroke-dasharray: 6 4
rx: 10
```

Legend content:

```text
Legend / 图例
OR Gate / 或门
AND Gate / 与门
Basic Event / 基本事件
```

Use the same symbols as the actual diagram.

---

### 7.9 Optional Instruction Panel

For templates used in workshops, include an optional instruction panel in the lower right.

Panel title:

```text
How to Use / 使用说明
```

Example steps:

```text
1. Define the top event.
2. Break it into major failure paths.
3. Use OR/AND gates to clarify logic.
4. Continue until basic events are testable.
```

This panel should be optional and disabled by default when the user asks for a compact diagram.

---

## 8. Color System

Use the same palette family as the fishbone template.

Recommended palette:

```text
primary_navy: #0B2E63
navy: #0B3A75
blue: #2F6FB6
light_blue: #DCEBFF
pale_blue: #F3F8FF
line_blue: #6E93BD
gray_text: #5B6B80
light_gray: #E6EDF5
background: #FFFFFF
background_soft: #F7FAFD
success_green: #4B8F5A
warning_orange: #D8902A
error_red: #C94A4A
```

Use red, green, or orange only for status annotations if needed. Do not overuse them in the base fault tree.

---

## 9. Typography

Preferred fonts:

```text
Arial, Helvetica, Microsoft YaHei, sans-serif
```

Text rules:

- Top Event: bold, high contrast.
- Intermediate Event: bold English label, smaller Chinese label.
- Basic Event: medium-weight English label, smaller Chinese label.
- Keep text horizontally oriented.
- Avoid rotated text.
- Avoid text overlap.
- Wrap long labels within boxes.

Recommended hierarchy:

```text
Title: 40-44 px
Subtitle: 24-28 px
Top Event: 24-28 px
Intermediate Event: 18-22 px
Basic Event: 16-18 px
Legend: 18-20 px
```

---

## 10. Input Schema

The generator should accept JSON input.

Recommended schema:

```json
{
  "diagram_type": "fault_tree",
  "title": "Fault Tree Analysis",
  "title_zh": "故障树分析",
  "subtitle": "Top Event - System Fails to Start",
  "subtitle_zh": "顶层事件 - 系统无法启动",
  "language": "bilingual",
  "output": "svg",
  "canvas": "16:9",
  "top_event": {
    "id": "T0",
    "label": "System Fails to Start",
    "label_zh": "系统无法启动",
    "icon": "warning"
  },
  "tree": {
    "gate": "OR",
    "children": [
      {
        "id": "1",
        "type": "intermediate_event",
        "label": "Power Issue",
        "label_zh": "电源问题",
        "icon": "power",
        "gate": "OR",
        "children": [
          {
            "id": "1.1",
            "type": "basic_event",
            "label": "No Power Supply",
            "label_zh": "无电源输入"
          },
          {
            "id": "1.2",
            "type": "basic_event",
            "label": "Power Module Fault",
            "label_zh": "电源模块故障"
          },
          {
            "id": "1.3",
            "type": "basic_event",
            "label": "Fuse Blown",
            "label_zh": "保险丝熔断"
          }
        ]
      },
      {
        "id": "2",
        "type": "intermediate_event",
        "label": "Control Unit Issue",
        "label_zh": "控制单元问题",
        "icon": "gear",
        "gate": "OR",
        "children": [
          {
            "id": "2.1",
            "type": "basic_event",
            "label": "Firmware Crash",
            "label_zh": "固件崩溃"
          },
          {
            "id": "2.2",
            "type": "basic_event",
            "label": "Controller Fault",
            "label_zh": "控制器故障"
          },
          {
            "id": "2.3",
            "type": "basic_event",
            "label": "Configuration Error",
            "label_zh": "配置错误"
          }
        ]
      },
      {
        "id": "3",
        "type": "intermediate_event",
        "label": "Start Signal Issue",
        "label_zh": "启动信号问题",
        "icon": "signal",
        "gate": "OR",
        "children": [
          {
            "id": "3.1",
            "type": "basic_event",
            "label": "Start Button Failure",
            "label_zh": "启动按钮故障"
          },
          {
            "id": "3.2",
            "type": "basic_event",
            "label": "Signal Line Disconnected",
            "label_zh": "信号线断开"
          },
          {
            "id": "3.3",
            "type": "basic_event",
            "label": "Sensor Fault",
            "label_zh": "传感器故障"
          }
        ]
      }
    ]
  },
  "show_legend": true,
  "show_instruction_panel": false,
  "style": "business_simple"
}
```

---

## 11. Natural Language Input Handling

If the user gives natural language instead of JSON, infer the structure.

Example user request:

```text
Create a business-simple fault tree for a system that fails to start. Main branches: power issue, control unit issue, and start signal issue.
```

The skill should infer:

```text
diagram_type = fault_tree
top_event = System Fails to Start
first-level events = Power Issue, Control Unit Issue, Start Signal Issue
gate = OR unless specified otherwise
```

Default assumptions:

- Use OR gates unless the user explicitly says conditions must happen together.
- Use bilingual output if the user mixes English and Chinese or asks in Chinese.
- Use three levels if enough detail is available.
- Use placeholder child events if the user only provides major branches.

---

## 12. Layout Algorithm Requirements

The implementation should be deterministic.

Recommended algorithm:

1. Parse the tree into levels.
2. Assign the top event to the top center.
3. Place first-level intermediate events evenly across the canvas width.
4. For each parent, place children evenly below it.
5. Reserve upper-left area for title and subtitle.
6. Reserve upper-right area for legend if enabled.
7. Avoid overlap between legend and diagram nodes.
8. Use orthogonal connector lines.
9. Wrap long text labels to fit within boxes.
10. If the tree is too wide, reduce font size slightly or increase horizontal spacing.

Supported first implementation scope:

```text
levels: 2-4
first-level events: 2-5
children per intermediate event: 1-4
canvas: 16:9 only
output: SVG only, PNG optional later
```

---

## 13. Output Requirements

Default output:

```text
SVG file
```

Optional output:

```text
PNG export
```

The SVG must:

- Open correctly in a browser.
- Be editable in vector tools where possible.
- Be suitable for inserting into PowerPoint.
- Use embedded SVG text, not rasterized text.
- Avoid external image dependencies.
- Use inline SVG shapes for icons or simple text/icon placeholders.

---

## 14. Suggested File Structure

Recommended skill structure after adding `fault_tree`:

```text
brainstorm-diagrams/
├─ SKILL.md
├─ scripts/
│  ├─ generate_diagram.py
│  ├─ generate_fishbone.py
│  └─ generate_fault_tree.py
├─ templates/
│  ├─ fishbone_business_simple.svg.j2
│  └─ fault_tree_business_simple.svg.j2
├─ examples/
│  ├─ fishbone.example.json
│  ├─ fault_tree.example.json
│  ├─ fishbone.output.svg
│  └─ fault_tree.output.svg
└─ references/
   ├─ visual_style_contract.md
   └─ fault_tree_spec.md
```

The top-level `generate_diagram.py` should dispatch by `diagram_type`:

```text
fishbone -> generate_fishbone.py
fault_tree -> generate_fault_tree.py
```

---

## 15. SKILL.md Update Guidance

Update the skill front matter to make the skill discoverable for both fishbone and fault tree use cases.

Recommended front matter:

```markdown
---
name: brainstorm-diagrams
description: Generate PPT-ready structured brainstorming and analysis diagrams, including business-simple fishbone diagrams and fault tree analysis diagrams for product design, process design, failure analysis, troubleshooting, and root-cause analysis.
---
```

Recommended diagram type section:

```markdown
## Supported Diagram Types

Current version supports:

- `fishbone`: divergent cause brainstorming and category-based problem decomposition.
- `fault_tree`: logical failure decomposition using top events, intermediate events, basic events, and AND/OR gates.

Future planned types:

- `exclusion_tree`: verification and elimination workflow.
- `cause_screening_matrix`: scoring, filtering, and prioritizing possible causes.
- `process_flow`: process design and workflow mapping.
- `swimlane`: cross-functional process mapping.
- `fmea`: failure mode and risk prioritization.
```

---

## 16. Validation Checklist

Before returning a generated `fault_tree` diagram, verify:

- The diagram is top-down.
- The top event is clearly visible and centered.
- AND/OR gates are visually distinct.
- The legend matches the gate symbols used in the diagram.
- Major events use rounded rectangles.
- Basic events are readable and aligned.
- Connectors are clean and not crossing unnecessarily.
- The visual style matches the business-simple fishbone template.
- The SVG opens successfully.
- No realistic, cartoon, or decorative illustration style is used.
- The diagram is suitable for PowerPoint.

---

## 17. Example Prompt for Codex

Use the following prompt to ask Codex to implement this extension:

```text
Extend the existing `brainstorm-diagrams` skill by adding a new diagram type: `fault_tree`.

The new template must generate a PPT-ready business-simple fault tree analysis diagram as SVG. It should visually match the existing fishbone template: white background, navy/light-blue corporate styling, rounded rectangles, simple line icons, thin connectors, and clean sans-serif typography.

Implement:
- JSON input parsing for `diagram_type = fault_tree`
- deterministic SVG generation
- a Jinja2 SVG template
- support for top event, intermediate events, basic events, and AND/OR gates
- optional legend
- example input JSON
- sample output SVG
- validation checks

Do not use raster AI image generation. Do not use cartoon or realistic graphics. Keep the output suitable for PowerPoint engineering and executive review.
```

---

## 18. Example Fault Tree Content

Default example topic:

```text
Top Event: System Fails to Start / 系统无法启动
```

First-level branches:

```text
1. Power Issue / 电源问题
2. Control Unit Issue / 控制单元问题
3. Start Signal Issue / 启动信号问题
```

Basic events:

```text
1.1 No Power Supply / 无电源输入
1.2 Power Module Fault / 电源模块故障
1.3 Fuse Blown / 保险丝熔断

2.1 Firmware Crash / 固件崩溃
2.2 Controller Fault / 控制器故障
2.3 Configuration Error / 配置错误

3.1 Start Button Failure / 启动按钮故障
3.2 Signal Line Disconnected / 信号线断开
3.3 Sensor Fault / 传感器故障
```

Default logic:

```text
Top Event = Power Issue OR Control Unit Issue OR Start Signal Issue
Each branch = one or more basic events connected by OR gate unless specified otherwise
```

---

## 19. Versioning Recommendation

Recommended version plan:

```text
v0.1: fishbone only
v0.2: add fault_tree
v0.3: add exclusion_tree
v0.4: add cause_screening_matrix
v0.5: add process_flow / swimlane
```

Do not implement all future diagram types at once. Keep the skill focused and reliable.
