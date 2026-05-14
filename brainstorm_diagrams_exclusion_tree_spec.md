# Spec: `brainstorm-diagrams` Template Extension — `exclusion_tree`

## 1. Purpose

This document specifies the `exclusion_tree` diagram type for the `brainstorm-diagrams` skill.

`exclusion_tree` is a PPT-ready troubleshooting and root-cause elimination diagram. It is used after brainstorming, fishbone analysis, or fault tree analysis to guide users through a sequence of checks that progressively eliminate impossible causes and narrow the issue down to the most likely root cause.

The first implementation of `brainstorm-diagrams` may still focus on `fishbone`. This document defines a future or next-version extension that should share the same visual language as the existing `fishbone` and `fault_tree` templates.

## 2. Skill Context

Skill name:

```text
brainstorm-diagrams
```

Diagram type:

```text
exclusion_tree
```

Relationship to other diagram types:

```text
fishbone               = divergent cause brainstorming
fault_tree             = logical failure decomposition
exclusion_tree         = verification and elimination workflow
cause_screening_matrix = scoring and prioritization
```

The `exclusion_tree` template should not replace `fishbone` or `fault_tree`. It should be used when the user wants to test, verify, exclude, or narrow down possible causes.

## 3. When to Use

Use `exclusion_tree` when the user asks for or implies:

- 排除树
- troubleshooting tree
- elimination tree
- exclusion workflow
- step-by-step cause elimination
- root cause verification flow
- issue diagnosis flow
- FA troubleshooting path
- failure investigation checklist
- “如何一步步排除原因”
- “how to narrow down possible causes”
- “how to verify and exclude these causes”

Typical scenarios:

- failure analysis
- product issue troubleshooting
- field return analysis
- customer complaint triage
- manufacturing process abnormality investigation
- equipment diagnostic flow
- engineering debug workflow
- process issue elimination

## 4. Conceptual Definition

An exclusion tree is a decision-tree-like diagram that starts from a top event or target problem, then walks through a sequence of test or check points.

Each checkpoint asks whether a specific condition is normal or abnormal.

Typical logic:

```text
Top Event / Target Problem
        ↓
Check Point 1: Is condition A OK?
   ├─ No / Fail  → likely cause or excluded/confirmed conclusion
   └─ Yes / Pass → continue to next check
                    ↓
              Check Point 2: Is condition B OK?
                 ├─ No / Fail  → likely cause
                 └─ Yes / Pass → continue
```

Compared with `fault_tree`:

- `fault_tree` explains what combinations of causes may lead to a failure.
- `exclusion_tree` tells users what to check first, second, and third to eliminate causes efficiently.

## 5. Visual Style

The `exclusion_tree` template must use the same overall business-simple style as the existing `fishbone` and `fault_tree` templates.

### 5.1 Overall style

- White or very light gray background.
- Corporate PPT-ready style.
- Clean vector shapes.
- Navy blue, light blue, gray, white, and limited red/green status accents.
- No hand-drawn, cartoon, 3D, decorative, or realistic visual elements.
- Use generous spacing and clear hierarchy.
- Suitable for executive review, engineering review, FA review, and workshop summary decks.

### 5.2 Shape language

Use only simple geometric shapes:

- rounded rectangles
- lines and elbow connectors
- small arrows
- status chips
- simple outline icons
- check/cross symbols
- optional legend cards

Avoid:

- organic shapes
- decorative blobs
- complex illustrations
- realistic objects
- excessive gradients
- heavy shadows
- cluttered flowchart symbols

### 5.3 Color palette

Recommended colors:

```text
navy_primary:       #0B3A75
navy_dark:          #08285A
blue_light:         #EAF3FF
blue_mid:           #6E93BD
gray_text:          #5B677A
gray_line:          #CBD5E1
gray_bg:            #F7FAFD
success_green:      #2E7D32
success_green_bg:   #EAF6EA
warning_red:        #C62828
warning_red_bg:     #FDECEC
neutral_bg:         #F8FBFF
```

Use red only for failed checks or confirmed abnormal causes. Use green only for passed checks or no-issue-found outcomes.

## 6. Layout Requirements

### 6.1 Canvas

Default canvas:

```text
width: 1920
height: 1080
ratio: 16:9
```

Default orientation:

```text
top-to-bottom with side branches
```

The main flow should move from the top event downward through checkpoints. Fail branches may extend to the right. Pass branches usually continue downward or diagonally downward-left depending on available space.

### 6.2 Recommended layout regions

```text
left / center: main exclusion tree
right top: legend
right bottom: usage note or summary box
```

Suggested layout:

```text
Title area:       x=60,   y=55
Main tree:        x=120,  y=120, width=1100, height=850
Legend:           x=1350, y=90,  width=430, height=260
How-to-use box:   x=1180, y=740, width=620, height=250
```

The tree must remain readable when inserted into PowerPoint.

### 6.3 Flow pattern

Default pattern:

1. Top event block at top center.
2. First checkpoint below the top event.
3. For each checkpoint:
   - `yes` / `pass` branch continues toward the next check.
   - `no` / `fail` branch points to a root-cause or likely-cause result card.
4. Final pass path ends in a green “no issue found in this path / consider other causes” card.

The default visual path should make it easy to follow the preferred troubleshooting sequence.

## 7. Node Types

### 7.1 Top Event Node

Purpose:

- Represents the target problem being investigated.

Visual:

- Rounded rectangle.
- Navy fill.
- White text.
- Optional simple warning icon.

Recommended dimensions:

```text
width: 300-360 px
height: 90-110 px
corner radius: 14-20 px
fill: #0B3A75
text: white
```

Example text:

```text
系统无法启动
Top Event
```

### 7.2 Check Point Node

Purpose:

- Represents a diagnostic step or verification question.

Visual:

- Rounded rectangle.
- Light blue fill.
- Navy border.
- Optional simple icon on the left.
- Bilingual text supported.

Recommended dimensions:

```text
width: 330-430 px
height: 80-95 px
corner radius: 12-16 px
fill: #EAF3FF
stroke: #0B3A75
stroke width: 2 px
```

Example text:

```text
1. 是否有电源输入？
Power Input OK?
```

Checkpoint labels should be written as testable questions.

Good examples:

- Power Input OK?
- Signal Line Connected?
- Firmware Version Correct?
- Temperature Within Spec?
- Material Batch Normal?

Avoid vague labels:

- Power issue
- Signal problem
- Bad firmware
- Maybe process problem

### 7.3 Pass / Fail Branch Chip

Purpose:

- Shows the result of a checkpoint.

Visual:

Pass chip:

```text
label: Yes / Pass / 是 / 通过
fill: #EAF6EA
stroke: #2E7D32
text: #2E7D32
```

Fail chip:

```text
label: No / Fail / 否 / 不通过
fill: #FDECEC
stroke: #C62828
text: #C62828
```

Recommended dimensions:

```text
width: 70-95 px
height: 34-42 px
corner radius: 8-10 px
```

### 7.4 Root Cause / Conclusion Card

Purpose:

- Shows a confirmed or likely cause when a check fails.

Visual:

- Rounded rectangle.
- Very light gray or white fill.
- Thin gray border.
- Red cross icon or red status marker.
- Bilingual conclusion text.

Recommended dimensions:

```text
width: 240-330 px
height: 120-170 px
corner radius: 12-16 px
fill: #FFFFFF or #F8FBFF
stroke: #CBD5E1
status icon: red circle with white cross
```

Example text:

```text
根因：
无电源输入

Root Cause:
No Power Input
```

### 7.5 No Issue Found Card

Purpose:

- Indicates that the current pass path did not identify the cause.

Visual:

- Rounded rectangle.
- Green accent.
- Light green background.
- Check icon.

Example text:

```text
未找到异常
考虑其他较不常见原因
或需要更深入分析

No issue found in this path.
Consider other rare causes
or deeper analysis.
```

## 8. Connectors

Use simple elbow connectors and directional arrows.

Requirements:

- Stroke: navy or blue-gray.
- Stroke width: 2 px.
- Arrowheads should be small and clean.
- Avoid crossing lines where possible.
- Align connectors to node centers.
- Pass path should be visually continuous.
- Fail branches should clearly lead to conclusion cards.

Recommended connector styles:

```text
main flow:  #0B3A75, 2 px
side branch: #0B3A75, 2 px
inactive / secondary: #6E93BD, 1.5 px
```

## 9. Legend

Include a legend by default if space allows.

Legend card visual:

- Rounded rectangle.
- White or very light fill.
- Dashed or thin navy border.
- Title: `Legend / 图例`.

Recommended legend items:

| Symbol | Meaning |
|---|---|
| Rounded blue node | Test Step / Check Point / 检验步骤 |
| Green chip | Yes / Pass / 是 / 通过 |
| Red chip | No / Fail / 否 / 不通过 |
| Red cross card | Excluded or confirmed abnormal cause / 被排除或确认的原因 |
| Green check card | No issue found / 未发现异常 |

## 10. How-to-use Note

Optionally include a small instruction card, especially for generated PPT visuals.

Default content:

```text
How to Use / 使用说明
1. Start from the top event.
2. Perform each check in sequence.
3. Follow Yes/No branches based on test results.
4. Stop when a failed check identifies a likely root cause.
5. If all checks pass, consider rare causes or deeper analysis.
```

In Chinese-English bilingual mode:

```text
排除树使用说明 / How to Use
1. 从顶层问题开始，依次执行检查步骤。
2. 根据检查结果（是/否）沿箭头向下走。
3. 当遇到“不通过/否”时，右侧原因可作为优先验证根因。
4. 若所有步骤均通过，则该路径未找到根因，需要考虑其他路径或更深入分析。
```

## 11. Input Schema

The implementation should support JSON input.

Recommended schema:

```json
{
  "diagram_type": "exclusion_tree",
  "title": "Exclusion Tree / 排除树",
  "problem": {
    "text_en": "System Fails to Start",
    "text_zh": "系统无法启动"
  },
  "language": "bilingual",
  "theme": "business_simple",
  "checks": [
    {
      "id": "1",
      "text_en": "Power Input OK?",
      "text_zh": "是否有电源输入？",
      "icon": "bolt",
      "pass_label_en": "Yes",
      "pass_label_zh": "是",
      "fail_label_en": "No",
      "fail_label_zh": "否",
      "fail_conclusion": {
        "text_en": "No Power Input",
        "text_zh": "无电源输入",
        "detail_en": "Check power cable and outlet.",
        "detail_zh": "检查电源线连接和插座供电。"
      }
    },
    {
      "id": "2",
      "text_en": "Power Module Output OK?",
      "text_zh": "电源模块输出是否正常？",
      "icon": "module",
      "fail_conclusion": {
        "text_en": "Power Module Fault",
        "text_zh": "电源模块故障"
      }
    }
  ],
  "final_pass_conclusion": {
    "text_en": "No issue found in this path. Consider other rare causes or deeper analysis.",
    "text_zh": "该路径未发现异常。考虑其他较不常见原因或进行更深入分析。"
  },
  "show_legend": true,
  "show_how_to_use": true,
  "output": "svg",
  "canvas": "16:9"
}
```

## 12. Natural Language Input Handling

If the user provides natural language instead of JSON:

1. Infer `diagram_type = exclusion_tree` from the request.
2. Extract the top event / target problem.
3. Extract or propose sequential checks.
4. Convert each check into a testable Yes/No question.
5. If no checks are provided, create a generic troubleshooting sequence based on the problem domain.
6. Ask for clarification only if the problem is too ambiguous to create meaningful checks.

Default categories for engineering troubleshooting may include:

- input / power / material availability
- interface / connection
- signal / measurement
- control / software / firmware
- process condition
- environment condition
- operator / method

## 13. Layout Algorithm

The implementation should be deterministic.

Recommended first version:

- Support 3–6 checkpoints.
- Main pass path flows downward on the left-center side.
- Each fail branch goes to the right of its checkpoint.
- If there are more than 4 checkpoints, reduce vertical spacing or generate a taller SVG.
- If conclusion text is long, wrap text inside cards.

Pseudo-layout:

```text
x_main = 650
x_fail = 1050
y_top = 140
checkpoint_gap_y = 160

Top event at (x_main, y_top)
Check 1 at (x_main, y_top + 150)
Check 2 at (x_main - 160, y_top + 310)
Check 3 at (x_main - 320, y_top + 470)
Check 4 at (x_main - 480, y_top + 630)

Fail conclusion for each check at x_fail, near the same y as the check.
Final pass conclusion at the bottom left.
```

The exact geometry may be improved, but the final diagram must be readable and aligned.

## 14. Icons

Use simple line icons only.

Allowed icon names:

```text
bolt
module
chip
signal
thermometer
gear
document
material
operator
check
cross
question
```

Icon rules:

- Icons must be simple SVG paths or minimal line icons.
- Use navy or white depending on background.
- Do not use detailed illustrations.
- Do not rely on external icon fonts unless bundled or generated inline.

## 15. Output Requirements

Default output:

```text
SVG
```

Optional output:

```text
PNG
```

The generated SVG must:

- Open in a browser.
- Be insertable into PowerPoint.
- Use common fonts only.
- Not depend on external network assets.
- Escape text safely.
- Preserve readable text at 16:9 slide size.

Recommended output files:

```text
output/exclusion_tree.svg
output/exclusion_tree.png
```

## 16. Suggested File Structure

```text
brainstorm-diagrams/
├─ SKILL.md
├─ scripts/
│  ├─ generate_fishbone.py
│  ├─ generate_fault_tree.py
│  └─ generate_exclusion_tree.py
├─ templates/
│  ├─ fishbone_business_simple.svg.j2
│  ├─ fault_tree_business_simple.svg.j2
│  └─ exclusion_tree_business_simple.svg.j2
├─ examples/
│  ├─ fishbone.example.json
│  ├─ fault_tree.example.json
│  ├─ exclusion_tree.example.json
│  └─ outputs/
└─ references/
   ├─ visual_style_contract.md
   └─ diagram_type_roadmap.md
```

## 17. Example Input

```json
{
  "diagram_type": "exclusion_tree",
  "title": "Exclusion Tree / 排除树",
  "problem": {
    "text_en": "System Fails to Start",
    "text_zh": "系统无法启动"
  },
  "language": "bilingual",
  "theme": "business_simple",
  "checks": [
    {
      "id": "1",
      "text_en": "Power Input OK?",
      "text_zh": "是否有电源输入？",
      "icon": "bolt",
      "fail_conclusion": {
        "text_en": "No Power Input",
        "text_zh": "无电源输入",
        "detail_en": "Check power cord, connector, and outlet.",
        "detail_zh": "检查电源线、连接器和插座供电。"
      }
    },
    {
      "id": "2",
      "text_en": "Power Module Output OK?",
      "text_zh": "电源模块输出是否正常？",
      "icon": "module",
      "fail_conclusion": {
        "text_en": "Power Module Fault",
        "text_zh": "电源模块故障"
      }
    },
    {
      "id": "3",
      "text_en": "Control Board OK?",
      "text_zh": "控制板是否正常工作？",
      "icon": "chip",
      "fail_conclusion": {
        "text_en": "Control Board Fault",
        "text_zh": "控制板故障"
      }
    },
    {
      "id": "4",
      "text_en": "Start Signal OK?",
      "text_zh": "启动信号是否正常？",
      "icon": "signal",
      "fail_conclusion": {
        "text_en": "Start Signal Issue",
        "text_zh": "启动信号异常"
      }
    }
  ],
  "final_pass_conclusion": {
    "text_en": "No issue found in this path. Consider other rare causes or deeper analysis.",
    "text_zh": "该路径未发现异常。考虑其他较不常见原因或进行更深入分析。"
  },
  "show_legend": true,
  "show_how_to_use": true,
  "output": "svg",
  "canvas": "16:9"
}
```

## 18. Quality Checks

Before completing generation, verify:

- The diagram type is clearly `exclusion_tree`.
- The top event is shown at the top.
- The main path flows downward through ordered checkpoints.
- Each checkpoint is phrased as a testable question.
- Yes/Pass branches continue the verification path.
- No/Fail branches lead to conclusion/root-cause cards.
- Red is used only for failed/abnormal conclusions.
- Green is used only for passed/no-issue conclusions.
- The diagram uses the same business-simple style as fishbone and fault_tree.
- The SVG contains no external asset dependencies.
- Text does not overlap.
- Connectors are aligned and readable.
- The output is suitable for PowerPoint.

## 19. Forbidden Outputs

Do not generate:

- a generic flowchart without elimination logic
- a fault tree with AND/OR gates instead of pass/fail checkpoints
- a fishbone diagram
- a decorative tree illustration
- a cartoon troubleshooting poster
- a dense engineering schematic that is not PPT-friendly
- shapes that look like realistic objects rather than abstract business diagram elements

## 20. Codex Implementation Prompt

Use the following prompt to implement the extension:

```text
Extend the `brainstorm-diagrams` skill with a new diagram type named `exclusion_tree`.

The template should generate a PPT-ready business-simple exclusion tree / troubleshooting decision tree as SVG.

The diagram must start with a top event at the top, then show a sequence of testable checkpoints. Each checkpoint has a Yes/Pass branch that continues to the next check and a No/Fail branch that leads to a root-cause or likely-cause conclusion card. The final pass path should end in a green no-issue-found card.

Use the same visual style as the existing fishbone and fault_tree templates: white or very light background, navy and light-blue corporate palette, rounded rectangles, clean thin connectors, simple line icons, and optional legend and how-to-use boxes.

Implement:
- `scripts/generate_exclusion_tree.py`
- `templates/exclusion_tree_business_simple.svg.j2`
- `examples/exclusion_tree.example.json`
- sample SVG output

The generator should accept JSON input, escape text safely, support bilingual English/Chinese labels, and produce deterministic SVG output suitable for PowerPoint.

Do not create a generic process flowchart. Do not use AND/OR gates. Do not use decorative tree illustrations. The diagram must clearly represent cause verification and elimination logic.
```

## 21. Version Roadmap

Recommended roadmap:

```text
v0.1 fishbone
v0.2 fault_tree
v0.3 exclusion_tree
v0.4 cause_screening_matrix
v0.5 process_flow / swimlane
```

`exclusion_tree` should be treated as the verification-and-elimination companion to `fault_tree`.

## 22. References for Skill Packaging

Codex skills are packaged as reusable workflow folders. Codex initially sees the skill metadata and loads the full `SKILL.md` only when it decides the skill is relevant. Keep the skill description concise and make each diagram type discoverable through clear keywords in the metadata and instructions.

