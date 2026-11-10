# Bias Schematic Illustration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Draw the common-emitter circuit as an inline SVG whose labels always equal the values used for the calculation, plus a one-line region verdict.

**Architecture:** `app.py` parses its `DEFAULTS` once into `app.DEFAULT_INPUTS` and passes a `diagram: BiasInputs` into the existing template. The template renders a static-shape SVG whose text nodes are filled from `diagram` through the existing `format_voltage` / `format_resistance` Jinja globals. CSS adds a two-column layout above 900 px. No JavaScript, no new dependency, no change to `bjt.py`.

**Tech Stack:** Python 3.12.7, Flask, Jinja2, inline SVG, plain CSS, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-dc-bias-design.md` (Addendum: schematic illustration)

## Global Constraints

- `git` is not on PATH: use `C:\Users\B6807757\AppData\Local\Programs\Git\cmd\git.exe`.
- Branch `main`, remote `origin`, identity `Poom <poomhirun2549@gmail.com>` (already configured).
- Do not modify `bjt.py`, `electrical.py`, `test_electrical.py`. No JavaScript, no new dependency.
- UI copy in Thai; symbols stay Latin (`VCC`, `R1`, `RC`, `Q1`, `β`).
- Numbers in the diagram come only from `format_voltage`, `format_resistance`, and `"%g"` for β.
- Run `python -m unittest -v` from the repo root; all four test files must stay green (currently 45).

## Review Focus

1. Diagram labels diverge from the computed result after a POST — the label must come from the same `BiasInputs` the solver used (Tasks 2 and 3).
2. Parse failure leaves the page with a stale or blank diagram — it must still render, from defaults, with a caption (Task 3).
3. A label containing a value like `1000` must use the formatter's unit promotion, not raw `str()` (Tasks 1–2).
4. Very long labels (e.g. `1.23 MΩ`) overflow the SVG viewBox (Task 1: fixed label anchors + `textLength`-free layout, checked visually).

---

### Task 1: Schematic markup with default values

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Modify: `static/style.css`
- Test: `test_app.py`

**Interfaces:**
- Consumes: `build_inputs`, `DEFAULTS`, `format_voltage`, `format_resistance` (all exist).
- Produces: `app.DEFAULT_INPUTS: BiasInputs`; template context key `diagram: BiasInputs`.

- [ ] **Step 1: Write the failing test**

```python
class TestDiagram(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_shows_schematic_with_default_values(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("<svg", body)
        self.assertIn('role="img"', body)
        for label in ("12.0 V", "47 kΩ", "10 kΩ", "2.2 kΩ", "1 kΩ"):
            with self.subTest(label=label):
                self.assertIn(label, body)
```

- [ ] **Step 2: Run it and watch it fail** → `python -m unittest test_app` fails: no `<svg` in the page.

- [ ] **Step 3: Implement**

In `app.py`, after `build_inputs`, add `DEFAULT_INPUTS = build_inputs(DEFAULTS)` and pass `diagram=DEFAULT_INPUTS` from the `GET` branch (leave `POST` unchanged for now).

In `templates/index.html`, add a `<section class="schematic">` holding an `<svg viewBox="0 0 320 400" role="img" aria-labelledby="schematic-title">` with `<title id="schematic-title">วงจรไบแอสแบบแบ่งแรงดัน common-emitter</title>`, and these parts, labelled from `diagram`:

| Part | Text |
|---|---|
| supply rail | `VCC = {{ format_voltage(diagram.vcc) }}` |
| `R1` | `R1` + `{{ format_resistance(diagram.r1) }}` |
| `R2` | `R2` + `{{ format_resistance(diagram.r2) }}` |
| `RC` | `RC` + `{{ format_resistance(diagram.rc) }}` |
| `RE` | `RE` + `{{ format_resistance(diagram.re) }}` |
| `Q1` | `Q1` + `NPN β = {{ "%g"|format(diagram.beta) }}` |

Draw with `<line>`/`<circle>` and `class` hooks only (no inline colours): rail at top, `R1` down to the base node, `R2` base node to ground, `RC` rail to collector, NPN symbol at centre-right with collector up and emitter down, `RE` emitter to ground, ground bars at the bottom, node dots at base/collector/emitter.

In `static/style.css`, style `.schematic` (card, centred), `.schematic svg` (max-width 320 px, height auto), `.schematic .wire` (`stroke: currentColor`, `stroke-width: 2`, `fill: none`), `.schematic .node` (`fill: currentColor`), `.schematic text` (`font: 12px/1 ui-monospace, Consolas, monospace; fill: currentColor`), `.schematic .label` (`font-weight: 600`).

- [ ] **Step 4: Run it and watch it pass** → `python -m unittest test_app` → all green.

- [ ] **Step 5: Commit** `feat: draw the bias schematic with the supplied values`

---

### Task 2: Diagram follows submitted values

**Files:**
- Modify: `app.py`
- Test: `test_app.py`

**Interfaces:**
- Consumes: `app.DEFAULT_INPUTS`, `result.inputs`.
- Produces: `POST /` passes `diagram=result.inputs` on success and `diagram=DEFAULT_INPUTS` on a `ValueError`.

- [ ] **Step 1: Write the failing test**

```python
    def test_diagram_follows_submitted_values(self):
        body = self.client.post("/", data={**FORM, "r1": "100k"}).get_data(as_text=True)
        self.assertIn("100 kΩ", body)
        self.assertIn("366 µA", body)
        self.assertNotIn("47 kΩ", body)
```

- [ ] **Step 2: Run it and watch it fail** → the page still shows `47 kΩ` and no `100 kΩ`.

- [ ] **Step 3: Implement** — in the `POST` branch set `diagram = result.inputs if result else DEFAULT_INPUTS` (after the `try/except`) and pass it to `render_template`.

- [ ] **Step 4: Run it and watch it pass** → `python -m unittest test_app` → all green.

- [ ] **Step 5: Commit** `feat: bind the schematic labels to the submitted values`

---

### Task 3: Default caption, region verdict, two-column layout

**Files:**
- Modify: `templates/index.html`
- Modify: `static/style.css`
- Test: `test_app.py`

**Interfaces:**
- Consumes: `error`, `result`, `diagram`.
- Produces: caption under the SVG when `error` is set; `.verdict` line inside the results block.

- [ ] **Step 1: Write the failing test**

```python
    def test_invalid_input_keeps_a_default_schematic(self):
        body = self.client.post("/", data={**FORM, "r1": "0"}).get_data(as_text=True)
        self.assertIn("<svg", body)
        self.assertIn("ค่าตั้งต้น", body)

    def test_active_result_shows_a_region_verdict(self):
        body = self.client.post("/", data=FORM).get_data(as_text=True)
        self.assertIn("โซนแอกทีฟปกติ", body)
        self.assertIn("7.76 V", body)
```

- [ ] **Step 2: Run it and watch it fail** → no `ค่าตั้งต้น`, no `โซนแอกทีฟปกติ`.

- [ ] **Step 3: Implement**

Under the SVG, `<p class="caption">` rendered only `{% if error %}` with the text `แผนภาพแสดงค่าตั้งต้น — แก้ไขค่าที่ไม่ถูกต้องก่อน`.

Inside `.results`, after the badge, add `{% if result.region == "active" %}<p class="verdict verdict-active">โซนแอกทีฟปกติ · VCE = {{ format_voltage(result.vce) }} &gt; 0.2 V</p>{% elif result.region == "saturation" %}<p class="verdict verdict-saturation">Q-point อยู่ในโซนอิ่มตัว · VCE = {{ format_voltage(result.vce) }} &lt; 0.2 V</p>{% else %}<p class="verdict verdict-cutoff">ทรานซิสเตอร์ตัดการทำงาน · IC = 0</p>{% endif %}`.

In `static/style.css`, wrap the existing content in a `.layout` grid: one column by default, `grid-template-columns: minmax(0, 1fr) 340px` at `min-width: 900px`, with `.schematic` in the second column and `align-self: start`. Add `.verdict` colours reusing `--active`, `--saturation`, `--cutoff`.

- [ ] **Step 4: Run it and watch it pass** → `python -m unittest -v` → all four files green.

- [ ] **Step 5: Commit** `feat: add region verdict and default-schematic caption`

---

### Task 4: Document, verify live, push

**Files:**
- Modify: `README.md`

**Interfaces:**
- Produces: pushed `main` and a verified live page.

- [ ] **Step 1: README** — in the ENG29 section, add one sentence that the page draws the circuit as SVG and its labels follow the entered values, and that the diagram falls back to defaults with a caption when input is invalid.

- [ ] **Step 2: Full suite** — `python -m unittest -v` → all four files green.

- [ ] **Step 3: Live check** — start `python app.py`, then:

```powershell
(Invoke-WebRequest http://127.0.0.1:5000).Content -match '<svg'
$r = Invoke-WebRequest http://127.0.0.1:5000 -Method POST -Body @{vcc='12';r1='100k';r2='10k';rc='2.2k';re='1k';beta='150';vbe='0.7'} -UseBasicParsing
$r.Content -match '100 kΩ'; $r.Content -match '366 µA'
```

Expected: `True` for all three. Then stop the server.

- [ ] **Step 4: Commit** `docs: document the schematic illustration`

- [ ] **Step 5: Push** — `git push origin main`; verify `git status -sb` shows `## main...origin/main`.

---

## Self-Review

**Spec coverage:** labels bound to `BiasInputs` (Tasks 1–2), default fallback (Task 3), region verdict (Task 3), layout (Task 3), docs and push (Task 4).

**Step scan:** each step is one action with one checkable result; no task transcribes a module.

**Type consistency:** `DEFAULT_INPUTS`, `diagram`, `format_voltage`, `format_resistance` and `result.inputs` are used identically in every task; `β` uses `"%g"` everywhere.

**Review Focus:** label drift (Task 2, Task 3 test), parse failure still renders (Task 3), unit promotion via the formatters (Task 1), long labels checked visually in Task 4's live check.

**Proportion:** four tasks against a one-page addendum; no task rewrites existing behaviour.
