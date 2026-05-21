# `brainstorm-diagrams` — FMEA Table Specification

## 1. Purpose

This specification defines the `fmea_table` diagram type for the `brainstorm-diagrams` skill.

The goal is to generate a clean, PPT-ready, business-simple FMEA table for engineering, product design, process design, manufacturing, quality, and reliability analysis.

`fmea_table` should help users identify potential failure modes, evaluate risk, prioritize actions, and track risk-reduction measures.

---

## 2. Diagram Identity

```json
{
  "diagram_type": "fmea_table",
  "style": "business_simple"
}
```

Recommended display name:

```text
FMEA / Failure Mode and Effects Analysis
失效模式与影响分析
```

---

## 3. Position in the `brainstorm-diagrams` System

`fmea_table` is a table-based engineering analysis diagram. It complements the existing diagram types:

```text
fishbone               = divergent cause brainstorming
fault_tree             = logical failure decomposition
exclusion_tree         = verification and elimination workflow
two_by_two_matrix      = quick screening and prioritization
roadmap_timeline       = phased planning and milestone tracking
flowchart              = process and decision-flow representation
fmea_table             = structured risk evaluation and action planning
```

Typical workflow:

```text
Fishbone / Fault Tree
identify potential causes and failure paths
        ↓
FMEA Table
evaluate risk, prioritize failure modes, define controls and actions
        ↓
Exclusion Tree / Validation Plan
verify or eliminate high-risk causes
        ↓
Roadmap / Timeline
track mitigation actions and completion milestones
```

---

## 4. When to Use

Use `fmea_table` when the user asks for:

- FMEA
- Failure Mode and Effects Analysis
- 失效模式与影响分析
- risk analysis table
- design risk analysis
- process risk analysis
- product reliability review
- failure risk scoring
- RPN table
- S/O/D scoring
- risk mitigation action plan
- DFMEA or PFMEA style table

Typical use cases:

- Product design review
- Reliability engineering
- Manufacturing process risk assessment
- Failure analysis follow-up
- Design verification planning
- Quality improvement
- New product introduction risk review
- Supplier/process evaluation

---

## 5. Scope

### 5.1 Current implementation scope

The first implementation should support a clean, simplified FMEA table suitable for PPT and engineering review.

It should support:

- DFMEA-like product/design FMEA
- PFMEA-like process FMEA
- Generic engineering FMEA
- Bilingual English/Chinese labels
- S/O/D scoring
- RPN calculation
- Risk-level classification
- Recommended actions
- Owner, target date, and status tracking

### 5.2 Out of scope for first implementation

Do not implement full AIAG-VDA compliance in the first version.

The first version does not need to support:

- Full AIAG-VDA seven-step form
- Action Priority AP tables
- Special characteristic classification
- Linked control plans
- Version approval workflows
- Audit trail
- Dynamic Excel formulas
- Database persistence

The output should be a static, presentation-ready SVG/PNG table, not a full FMEA management system.

---

## 6. Visual Style

The visual style must match the existing `brainstorm-diagrams` business-simple system.

### 6.1 Overall style

- White or very light gray background.
- Corporate, clean, neutral presentation style.
- Main colors: navy blue, light blue, gray, white.
- Red, orange, and green should be used only for risk/status indicators.
- No heavy decoration.
- No hand-drawn style.
- No cartoon style.
- No 3D or photorealistic elements.
- Suitable for executive review, engineering design review, and PPT insertion.

### 6.2 Recommended palette

```text
Navy:          #0B3A75
Deep Navy:     #062B5F
Light Blue:    #EAF3FF
Border Blue:   #AFC7E8
Grid Gray:     #D8E0EA
Text Navy:     #082A55
Muted Gray:    #6B778C
Low Risk Green:#2E8B57
Medium Orange: #E99A1A
High Risk Red: #C7352E
Soft Red Fill: #FDECEC
Soft Amber:    #FFF4DF
Soft Green:    #EAF7EF
```

### 6.3 Typography

Use common fonts:

```text
Arial, Helvetica, Microsoft YaHei, sans-serif
```

Recommended hierarchy:

- Page title: 42–52 px, bold, navy.
- Subtitle / goal: 20–24 px.
- Table header: 15–18 px, bold, white text on navy fill.
- Table body: 13–16 px.
- Chinese secondary text: 1–2 px smaller than English text.
- Notes / footnotes: 12–14 px.

---

## 7. Canvas and Layout

### 7.1 Default canvas

```json
{
  "width": 1920,
  "height": 1080,
  "aspect_ratio": "16:9"
}
```

### 7.2 Recommended layout

The diagram should use a single-slide layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ Title + Goal                                  Rating / RPN Box │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Main FMEA Table                                               │
│                                                              │
├───────────────────────────┬──────────────────────────────────┤
│ Risk Priority Guide        │ Notes / Review Info              │
└───────────────────────────┴──────────────────────────────────┘
```

The main table should occupy most of the slide. Supporting panels should remain compact.

---

## 8. Required Table Columns

The default FMEA table should include the following columns:

| Column | Field Name | Description |
|---|---|---|
| Item / Function | `item_function` | Product module, function, process step, or system element |
| Potential Failure Mode | `failure_mode` | How the item/process could fail |
| Potential Effect(s) of Failure | `failure_effects` | What happens if the failure occurs |
| Potential Cause(s) / Mechanism(s) | `failure_causes` | Why the failure could occur |
| Current Controls - Prevention | `prevention_controls` | Existing controls that prevent the failure |
| Current Controls - Detection | `detection_controls` | Existing controls that detect the failure |
| S | `severity` | Severity score |
| O | `occurrence` | Occurrence score |
| D | `detection` | Detection score |
| RPN | `rpn` | Risk Priority Number |
| Recommended Actions | `recommended_actions` | Actions to reduce risk |
| Owner | `owner` | Responsible person/team |
| Target Completion | `target_completion` | Target date |
| Status | `status` | Current action status |

### 8.1 Optional columns

The generator may support optional columns, but they should be disabled by default to avoid overcrowding:

- `requirement`
- `classification`
- `design_owner`
- `process_owner`
- `verification_plan`
- `post_action_severity`
- `post_action_occurrence`
- `post_action_detection`
- `post_action_rpn`
- `remarks`

---

## 9. Scoring Rules

### 9.1 Default scale

Use a 1–10 scale by default:

```text
Severity   S: 1 = no effect, 10 = hazardous / severe impact
Occurrence O: 1 = remote,    10 = very high likelihood
Detection  D: 1 = almost certain detection, 10 = unlikely to detect
```

### 9.2 RPN calculation

The default formula is:

```text
RPN = S × O × D
```

Example:

```text
S = 8, O = 4, D = 5 → RPN = 160
```

### 9.3 Risk classification

Default thresholds:

| RPN Range | Risk Level | Visual Style | Recommended Action |
|---:|---|---|---|
| `>= 200` | High Risk | Red chip / red-tinted cell | Immediate action required |
| `100–199` | Medium Risk | Orange chip / amber-tinted cell | Plan and track action |
| `< 100` | Low Risk | Green chip / green-tinted cell | Monitor and maintain |

These thresholds should be configurable.

---

## 10. Status Values

Recommended default status values:

```text
Not Started
In Progress
Planned
Completed
Blocked
High Risk
```

Visual conventions:

| Status | Style |
|---|---|
| Completed | Green check icon / green chip |
| In Progress | Orange circle / orange chip |
| Planned | Blue or gray dot |
| Not Started | Gray dot |
| Blocked | Red warning icon |
| High Risk | Red warning chip |

---

## 11. Input Schema

### 11.1 Minimal input

```json
{
  "diagram_type": "fmea_table",
  "title": "FMEA / Failure Mode and Effects Analysis",
  "subtitle": "失效模式与影响分析",
  "goal": "Identify potential failure modes, evaluate risks, and define actions to prevent or reduce failures.",
  "rows": [
    {
      "item_function": "Power Supply / 电源模块",
      "failure_mode": "Output voltage out of spec / 输出电压超差",
      "failure_effects": [
        "Device may not start / 设备无法启动",
        "Unexpected reset / 异常复位"
      ],
      "failure_causes": [
        "Component tolerance drift / 元件参数漂移",
        "Poor voltage regulation / 调压无效"
      ],
      "prevention_controls": [
        "Derating design / 降额设计",
        "Use qualified LDO / 使用合格 LDO"
      ],
      "detection_controls": [
        "ICT functional test / ICT 功能测试",
        "Voltage monitoring in firmware / 固件电压监控"
      ],
      "severity": 8,
      "occurrence": 4,
      "detection": 5,
      "recommended_actions": [
        "Improve regulation circuit / 优化调压电路",
        "Add input voltage monitor / 增加输入电压监控"
      ],
      "owner": "Hardware Team",
      "target_completion": "2025-06-30",
      "status": "In Progress"
    }
  ]
}
```

### 11.2 Full input

```json
{
  "diagram_type": "fmea_table",
  "fmea_type": "design",
  "style": "business_simple",
  "language": "bilingual",
  "title": "FMEA / Failure Mode and Effects Analysis",
  "subtitle": "失效模式与影响分析",
  "goal": "Identify potential failure modes, evaluate risks, and define actions to prevent or reduce failures.",
  "project": {
    "name": "Next Generation Product",
    "owner": "Quality Engineering",
    "review_frequency": "Quarterly",
    "last_review_date": "2025-05-15"
  },
  "scoring": {
    "scale": "1-10",
    "formula": "RPN = S × O × D",
    "thresholds": {
      "high": 200,
      "medium": 100
    }
  },
  "columns": {
    "show_icons": true,
    "show_owner": true,
    "show_target_completion": true,
    "show_status": true,
    "show_post_action_scores": false
  },
  "rows": [],
  "notes": [
    "Reassess S, O, D after implementing actions to verify risk reduction.",
    "FMEA is a living document and should be updated throughout the product lifecycle."
  ]
}
```

---

## 12. Natural Language Inference Rules

The skill should infer `fmea_table` when the user asks for risk scoring or failure-mode analysis.

Examples:

| User request | Inferred diagram |
|---|---|
| "Make an FMEA for this product" | `fmea_table` |
| "帮我做一个失效模式和影响分析表" | `fmea_table` |
| "List failure modes, causes, effects, and RPN" | `fmea_table` |
| "Score these risks using severity occurrence detection" | `fmea_table` |
| "把这些 failure modes 做成工程评审表" | `fmea_table` |

If the user provides possible causes from a fishbone or fault tree and asks for scoring, infer `fmea_table` if they mention S/O/D, RPN, failure mode, effect, controls, or mitigation action.

If the user only asks for quick screening by two dimensions, use `two_by_two_matrix` instead.

---

## 13. SVG Generation Requirements

### 13.1 Output formats

Default output:

```text
SVG
```

Optional output:

```text
PNG
```

SVG is preferred because it is scalable and suitable for PowerPoint.

### 13.2 Deterministic generation

The diagram must be generated deterministically from input data.

Do not use AI image generation in the implementation.

### 13.3 Text escaping

All user-provided text must be safely escaped before insertion into SVG.

### 13.4 Auto-calculation

If `rpn` is not provided, calculate it automatically:

```text
rpn = severity * occurrence * detection
```

If any of S/O/D are missing, leave RPN blank and show a warning note if appropriate.

---

## 14. Layout Behavior

### 14.1 Row count

The default slide should support approximately 4–8 rows.

If there are more than 8 rows:

- Either shrink font size slightly,
- or split into multiple pages/slides,
- or create a scroll-independent long SVG if requested.

For PPT use, prefer multiple pages over unreadably small text.

### 14.2 Long text

Long text should wrap within cells.

For bullet-list fields, render each item as a compact bullet line.

Examples:

- Failure causes
- Prevention controls
- Detection controls
- Recommended actions

### 14.3 Cell highlighting

The RPN column should be visually emphasized:

- High risk: soft red cell fill.
- Medium risk: soft amber cell fill.
- Low risk: soft green or neutral fill.

Do not over-color the entire table.

---

## 15. Components

Implement the diagram using reusable SVG components:

```text
PageTitle
GoalText
RatingScalePanel
RpnGuidePanel
FmeaTable
TableHeaderCell
TableBodyCell
BulletListCell
RiskScoreCell
StatusChip
RiskPriorityGuide
NotesPanel
ReviewInfoPanel
```

---

## 16. Recommended Directory Structure

```text
brainstorm-diagrams/
├─ SKILL.md
├─ references/
│  ├─ visual_style_contract.md
│  ├─ fmea_table_spec.md
│  └─ fmea_table_reference.png
├─ templates/
│  └─ fmea_table.svg.j2
├─ examples/
│  ├─ fmea_table_input.example.json
│  └─ fmea_table_output.example.svg
└─ scripts/
   └─ generate_diagram.py
```

If `generate_diagram.py` already exists, extend it instead of creating a separate generator.

---

## 17. Example Data

Use the following sample rows for development/testing:

```json
[
  {
    "item_function": "Power Supply / 电源模块",
    "failure_mode": "Output voltage out of spec / 输出电压超差",
    "failure_effects": ["Device may not start / 设备无法启动", "Unexpected reset / 异常复位"],
    "failure_causes": ["Component tolerance drift / 元件参数漂移", "Poor voltage regulation / 调压无效"],
    "prevention_controls": ["Derating design / 降额设计", "Use qualified LDO / 使用合格 LDO"],
    "detection_controls": ["ICT functional test / ICT 功能测试", "Voltage monitoring in firmware / 固件电压监控"],
    "severity": 8,
    "occurrence": 4,
    "detection": 5,
    "recommended_actions": ["Improve regulation circuit / 优化调压电路", "Add input voltage monitor / 增加输入电压监控"],
    "owner": "Hardware Team",
    "target_completion": "2025-06-30",
    "status": "In Progress"
  },
  {
    "item_function": "Connector / 连接器",
    "failure_mode": "Intermittent connection / 间歇性连接",
    "failure_effects": ["Signal loss / 信号丢失", "Device reset / 设备复位"],
    "failure_causes": ["Loose mating / 接触不良", "Vibration or shock / 振动或冲击"],
    "prevention_controls": ["Specify retention force / 规定保持力", "Use locking design / 使用锁扣设计"],
    "detection_controls": ["Functional test / 功能测试", "Visual inspection / 目视检查"],
    "severity": 7,
    "occurrence": 5,
    "detection": 4,
    "recommended_actions": ["Change to locking connector / 更换为锁扣连接器", "Add go/no-go gauge / 增加通止规"],
    "owner": "Mechanical Team",
    "target_completion": "2025-07-15",
    "status": "Planned"
  },
  {
    "item_function": "Cooling Fan / 散热风扇",
    "failure_mode": "Fan not spinning / 风扇不转",
    "failure_effects": ["Overheating / 过热", "Performance degradation / 性能下降"],
    "failure_causes": ["Bearing wear / 轴承磨损", "Dust blockage / 灰尘堵塞"],
    "prevention_controls": ["Use long-life fan / 使用长寿命风扇", "Dust filter / 防尘滤网"],
    "detection_controls": ["RPM monitoring / 转速监控", "System temperature monitor / 系统温度监控"],
    "severity": 8,
    "occurrence": 6,
    "detection": 7,
    "recommended_actions": ["Add RPM alarm / 增加转速告警", "Add redundant fan option / 增加冗余风扇"],
    "owner": "Thermal Team",
    "target_completion": "2025-07-31",
    "status": "High Risk"
  }
]
```

---

## 18. Reference Visual Requirements

The reference visual should resemble a polished corporate FMEA slide:

- Large title at top-left.
- Compact rating scale and RPN guide at top-right.
- Main table occupying the central region.
- Navy table header.
- Thin gray grid lines.
- Risk score columns narrow and centered.
- RPN column emphasized.
- Recommended actions column wide enough for bullet lists.
- Bottom priority guide with red/orange/green chips.
- Notes and review info in compact panels.

---

## 19. Forbidden Output

Do not generate:

- A tree diagram.
- A fishbone diagram.
- A flowchart.
- A decorative poster with no usable table.
- A spreadsheet-looking page with no visual hierarchy.
- A compliance-heavy FMEA form that is unreadable in PPT.
- A layout that uses too many colors.
- A layout where RPN and actions are not visible.

---

## 20. Codex Implementation Prompt

Use the following prompt to implement the feature:

```text
Extend the `brainstorm-diagrams` skill with a new diagram type named `fmea_table`.

The diagram should generate a clean, PPT-ready FMEA table as SVG, with optional PNG export.

Visual style must match the existing business-simple system used by fishbone, fault_tree, exclusion_tree, two_by_two_matrix, roadmap_timeline, and flowchart:
- white or very light background
- navy blue headers
- light blue/gray grid lines
- clean sans-serif typography
- red/orange/green only for risk/status indicators
- no decorative or realistic imagery

Implement the default FMEA columns:
- Item / Function
- Potential Failure Mode
- Potential Effect(s) of Failure
- Potential Cause(s) / Mechanism(s)
- Current Controls (Prevention)
- Current Controls (Detection)
- S
- O
- D
- RPN
- Recommended Actions
- Owner
- Target Completion
- Status

Automatically calculate RPN = S × O × D when all three scores are provided.
Apply default risk thresholds:
- RPN >= 200: High Risk
- 100 <= RPN < 200: Medium Risk
- RPN < 100: Low Risk

Create reusable SVG components for title, rating scale panel, RPN guide, table header, table body rows, bullet-list cells, risk score cells, status chips, notes, and priority guide.

Support bilingual text and safe SVG escaping.
Support 4–8 rows on one 16:9 slide. For more rows, split into multiple pages or reduce density only within readable limits.

Add example input JSON and an example output SVG.
Update SKILL.md so natural language requests for FMEA, failure mode analysis, RPN, or S/O/D scoring route to `diagram_type = fmea_table`.
```

---

## 21. Acceptance Criteria

The implementation is acceptable when:

1. `diagram_type = fmea_table` generates a valid SVG.
2. The output visually matches the business-simple style system.
3. RPN is calculated correctly.
4. Risk levels are classified correctly.
5. The table includes all required columns by default.
6. Long text wraps cleanly inside cells.
7. The slide is readable at 16:9 PPT size.
8. Red/orange/green are used only for risk/status indicators.
9. The SVG opens in a browser.
10. The output can be inserted into PowerPoint without loss of readability.
11. The generator handles bilingual English/Chinese labels.
12. The table does not look like a raw spreadsheet dump.

---

## 22. Version Recommendation

Suggested version placement:

```text
v0.1 fishbone
v0.2 fault_tree
v0.3 exclusion_tree
v0.4 two_by_two_matrix
v0.5 roadmap_timeline
v0.6 flowchart
v0.7 fmea_table
```

Future related diagram types:

```text
cause_screening_matrix
decision_matrix
morphological_matrix
qfd_house_of_quality
sipoc
tradeoff_matrix
validation_plan_matrix
```
## Repo Implementation Notes (v0.6 core release)

This repository implements `diagram_type: fmea_table` as a simplified FMEA table diagram first.

- Scope for the first release: SVG renderer, JSON/Markdown templates, work creation/render scripts, PNG export, maintained testcases, and stresscases.
- Not in the first release: browser-builder page, natural-language extraction, post-action S/O/D columns, action priority/AP, control-plan workflow, or full AIAG-VDA compliance.
- Default language is single-language. Use `language: en`, `language: zh`, or `language: auto`; bilingual output should be explicit, not automatic.
- Dense tables extend the SVG height instead of shrinking the font or splitting pages.
- Markdown uses row sections (`## Row F1`) with key-value fields and bullets, not one large Markdown table.
- RPN defaults to `severity * occurrence * detection`. Default risk thresholds are high `>= 200`, medium `100-199`, and low `< 100`.
- The reference image is stored at `assets/fmea_table/FMEA diagram by image2.png`.
