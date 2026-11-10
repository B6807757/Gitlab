# BJT Common-Emitter DC Bias Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a small Flask app that computes the DC operating point of a voltage-divider-biased common-emitter stage, warns about cutoff/saturation, and cross-checks the result against a second independent derivation.

**Architecture:** All engineering lives in `bjt.py` as frozen dataclasses and pure functions (Thévenin closed form + nodal linear system solved by Gaussian elimination, no NumPy). `app.py` owns only form parsing and the one route, and renders `templates/index.html` with `static/style.css`. Tests use `unittest` and the Flask test client.

**Tech Stack:** Python 3.12.7, Flask (only external dependency), `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-dc-bias-design.md`

## Global Constraints

- Python 3.12.7. Only external dependency: Flask (`flask>=3.0,<4`). No NumPy, no JS.
- `git` is not on PATH. Use `C:\Users\B6807757\AppData\Local\Programs\Git\cmd\git.exe` for every git command.
- Repo-local git identity: `Poom` / `poomhirun2549@gmail.com`. Branch `main`, remote `origin`.
- All new files at the repo root. Do not modify `electrical.py`, `test_electrical.py`.
- Run tests with `python -m unittest -v` from the repo root; it must run all four test files.
- `VCE_SAT_V = 0.2` volts, stiff-divider factor `10`.
- UI copy in Thai; symbols stay Latin (`VCC`, `IC`, `VCE`, `IB`, `IE`, `RB`, `VBB`).
- Display 3 significant figures via `format(x, "#.3g")`.
- Inputs are in volts, ohms and plain numbers. Regions are `"cutoff" | "active" | "saturation"`.

## Review Focus

Inputs and conditions the spec implies but no task's happy path exercises; each gets a test in the owning task below.

1. `beta` at or below the floor — `0` and `0.5` must be rejected, `1` must be accepted and must not divide by zero (Task 1).
2. `RE = 0` or `RC = 0` — zero emitter resistance otherwise divides by zero or reports a nonsense Q-point; must be a validation error (Task 1), and `RE` also appears in every solver denominator (Task 2).
3. Non-finite input (`nan`, `inf`) — must raise a Thai `ValueError`, never propagate into the result (Task 1); a huge but finite value (`1e308`) must return a cutoff result without hanging or overflowing (Task 4).
4. Region boundaries — `VBB == VBE` must be cutoff, `VCE == 0.2` must be active (not saturation), `VCE == 1.0` must not warn, `VCE == 0.1999` must saturate (Task 4).
5. Text students actually type — `47k`, `4.7k`, `1M`, `47kΩ` parse; `4.7*1000`, `47,000`, empty string and `abc` are rejected with a readable message, not a 500 (Task 7).

---

### Task 0: Commit the design and set up git identity

**Files:**
- Create: `docs/superpowers/specs/2026-11-10-bjt-ce-dc-bias-design.md` (already written)
- Create: `docs/superpowers/plans/2026-11-10-bjt-ce-dc-bias.md` (this file)

**Interfaces:**
- Produces: a configured repo and `git log` evidence that identity and path both work.

- [ ] **Step 1: Set repo-local identity**

```powershell
& "C:\Users\B6807757\AppData\Local\Programs\Git\cmd\git.exe" config user.name "Poom"
& "C:\Users\B6807757\AppData\Local\Programs\Git\cmd\git.exe" config user.email "poomhirun2549@gmail.com"
```

- [ ] **Step 2: Commit the documents**

```powershell
& "C:\...\git.exe" add docs/superpowers
& "C:\...\git.exe" commit -m "docs: add BJT CE DC bias design and plan"
```

- [ ] **Step 3: Verify**

Run: `git log -1 --format="%h %an <%ae> %s"` → author is `Poom <poomhirun2549@gmail.com>`.

---

### Task 1: Inputs and validation

**Files:**
- Create: `bjt.py`
- Test: `test_bjt.py`

**Interfaces:**
- Produces: `bjt.BiasInputs(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float)` — frozen dataclass; `bjt.validate(inputs: BiasInputs) -> None` raising `ValueError` with a Thai message naming the field.

- [ ] **Step 1: Write the failing test**

```python
import unittest
from bjt import BiasInputs, validate

VALID = dict(vcc=12.0, r1=47000.0, r2=10000.0, rc=2200.0, re=1000.0, beta=150.0, vbe=0.7)


class TestValidation(unittest.TestCase):
    def test_accepts_reference_values(self):
        validate(BiasInputs(**VALID))

    def test_accepts_beta_of_one(self):
        validate(BiasInputs(**{**VALID, "beta": 1.0}))

    def test_rejects_non_positive_supply_and_resistors(self):
        for field in ("vcc", "r1", "r2", "rc", "re"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    validate(BiasInputs(**{**VALID, field: 0.0}))
                with self.assertRaises(ValueError):
                    validate(BiasInputs(**{**VALID, field: -1.0}))

    def test_error_names_the_field(self):
        with self.assertRaises(ValueError) as ctx:
            validate(BiasInputs(**{**VALID, "r1": 0.0}))
        self.assertIn("R1", str(ctx.exception))

    def test_rejects_beta_below_one(self):
        for beta in (0.0, 0.5):
            with self.subTest(beta=beta):
                with self.assertRaises(ValueError):
                    validate(BiasInputs(**{**VALID, "beta": beta}))

    def test_rejects_vbe_outside_range(self):
        for vbe in (-0.1, 12.0, 13.0):
            with self.subTest(vbe=vbe):
                with self.assertRaises(ValueError):
                    validate(BiasInputs(**{**VALID, "vbe": vbe}))

    def test_rejects_non_finite_values(self):
        for value in (float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate(BiasInputs(**{**VALID, "r2": value}))
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python -m unittest test_bjt -v` → `ModuleNotFoundError` / `ImportError: cannot import name 'BiasInputs'`.

- [ ] **Step 3: Implement in `bjt.py`**

`BiasInputs` is a frozen dataclass. `validate` checks, in order: every field finite (`math.isfinite`), `vcc > 0`, each of `r1, r2, rc, re > 0`, `beta >= 1`, `0 <= vbe < vcc`. Each failure raises `ValueError` with the field's Latin label (`VCC`, `R1`, `R2`, `RC`, `RE`, `β`, `VBE`) and a Thai reason, e.g. `"R1 ต้องมากกว่า 0"`, `"β ต้องไม่น้อยกว่า 1"`, `"VBE ต้องอยู่ระหว่าง 0 ถึง VCC"`.

- [ ] **Step 4: Run it and watch it pass**

Run: `python -m unittest test_bjt -v` → 7 tests, OK.

- [ ] **Step 5: Commit**

```powershell
git add bjt.py test_bjt.py
git commit -m "feat: add BJT bias inputs with validation"
```

---

### Task 2: Thévenin closed form

**Files:**
- Modify: `bjt.py`
- Test: `test_bjt.py`

**Interfaces:**
- Consumes: `BiasInputs`.
- Produces: `bjt.thevenin_equivalent(inputs) -> tuple[float, float]` returning `(vbb, rb)`; `bjt.solve_thevenin(inputs) -> dict[str, float]` with keys `ib, ic, ie, vb, ve, vc, vce`. Assumes the active region; the caller gates cutoff.

- [ ] **Step 1: Write the failing test**

```python
from bjt import solve_thevenin, thevenin_equivalent


class TestThevenin(unittest.TestCase):
    def test_equivalent(self):
        vbb, rb = thevenin_equivalent(BiasInputs(**VALID))
        self.assertAlmostEqual(vbb, 2.1052632, delta=1e-6)
        self.assertAlmostEqual(rb, 8245.614, delta=1e-2)

    def test_reference_qpoint(self):
        r = solve_thevenin(BiasInputs(**VALID))
        self.assertAlmostEqual(r["ib"], 8.8245e-6, delta=1e-9)
        self.assertAlmostEqual(r["ic"], 1.323675e-3, delta=1e-8)
        self.assertAlmostEqual(r["ie"], 1.33249e-3, delta=1e-8)
        self.assertAlmostEqual(r["vb"], 2.0325, delta=1e-4)
        self.assertAlmostEqual(r["ve"], 1.33249, delta=1e-4)
        self.assertAlmostEqual(r["vc"], 9.087915, delta=1e-4)
        self.assertAlmostEqual(r["vce"], 7.755425, delta=1e-4)

    def test_kirchhoff_holds(self):
        r = solve_thevenin(BiasInputs(**VALID))
        self.assertAlmostEqual(r["ib"] + r["ic"], r["ie"], delta=1e-12)
```

- [ ] **Step 2: Run it and watch it fail** → `ImportError: cannot import name 'solve_thevenin'`.

- [ ] **Step 3: Implement** the spec's equations verbatim:

```python
VBB = vcc * r2 / (r1 + r2)
RB  = r1 * r2 / (r1 + r2)
IB  = (VBB - vbe) / (RB + (1 + beta) * re)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * re
VC  = vcc - IC * rc
VB  = VE + vbe
VCE = VC - VE
```

- [ ] **Step 4: Run it and watch it pass** → `python -m unittest test_bjt -v`, all OK.

- [ ] **Step 5: Commit** `feat: add Thevenin closed-form bias solver`

---

### Task 3: Nodal solver and the agreement measure

**Files:**
- Modify: `bjt.py`
- Test: `test_bjt.py`

**Interfaces:**
- Consumes: `BiasInputs`.
- Produces: `bjt.solve_linear_system(a: list[list[float]], b: list[float]) -> list[float]` (Gaussian elimination, partial pivoting, raises `ValueError` on a singular matrix); `bjt.solve_nodal(inputs) -> dict[str, float]` with the same seven keys as `solve_thevenin`; `bjt.relative_difference(a: dict, b: dict) -> float`.

- [ ] **Step 1: Write the failing test**

```python
from bjt import relative_difference, solve_linear_system, solve_nodal


class TestNodal(unittest.TestCase):
    def test_gaussian_elimination(self):
        x = solve_linear_system([[2.0, 1.0], [1.0, -1.0]], [5.0, 1.0])
        self.assertAlmostEqual(x[0], 2.0)
        self.assertAlmostEqual(x[1], 1.0)

    def test_singular_system_raises(self):
        with self.assertRaises(ValueError):
            solve_linear_system([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])

    def test_agrees_with_thevenin_on_fixtures(self):
        fixtures = (
            VALID,
            {**VALID, "rc": 47000.0},
            {**VALID, "r1": 70000.0, "re": 100.0},
            {**VALID, "r1": 1000.0, "r2": 10000.0, "rc": 10.0, "re": 10.0, "beta": 10.0},
        )
        for fixture in fixtures:
            with self.subTest(fixture=fixture):
                inputs = BiasInputs(**fixture)
                diff = relative_difference(solve_thevenin(inputs), solve_nodal(inputs))
                self.assertLess(diff, 1e-9)
```

- [ ] **Step 2: Run it and watch it fail** → `ImportError`.

- [ ] **Step 3: Implement** the 3×3 system over unknowns `[VB, VC, IC]`:

```
1) (VB - VCC)/R1 + VB/R2 + IC/beta                 = 0
2) (VCC - VC)/RC - IC                              = 0
3) (VB - VBE)/RE - ((beta+1)/beta) * IC            = 0
```

Then `VE = VB - VBE`, `VCE = VC - VE`, `IB = IC/beta`, `IE = IC + IB`. Build the matrix as floats in one pass; do not reuse any Thévenin helper. Gaussian elimination with partial pivoting and a `1e-12` pivot tolerance. `relative_difference` returns `max(|a[k]-b[k]| / max(|a[k]|, 1e-12))` over the shared keys.

- [ ] **Step 4: Run it and watch it pass** → `python -m unittest test_bjt -v`, all OK.

- [ ] **Step 5: Commit** `feat: add independent nodal solver and agreement check`

---

### Task 4: Region classification and `analyze`

**Files:**
- Modify: `bjt.py`
- Test: `test_bjt.py`

**Interfaces:**
- Consumes: `validate`, `thevenin_equivalent`, `solve_thevenin`, `solve_nodal`, `relative_difference`.
- Produces: `bjt.VCE_SAT_V = 0.2`; `bjt.classify_region(vbb: float, vbe: float, vce: float) -> str`; `bjt.BiasResult` frozen dataclass with fields `inputs, vbb, rb, ib, ic, ie, vb, ve, vc, vce, region, warnings, ic_thevenin, ic_nodal, max_rel_diff, ic_sat`; `bjt.analyze(inputs: BiasInputs) -> BiasResult`.

- [ ] **Step 1: Write the failing test**

```python
from bjt import VCE_SAT_V, analyze, classify_region


class TestRegion(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(classify_region(vbb=0.7, vbe=0.7, vce=12.0), "cutoff")
        self.assertEqual(classify_region(vbb=1.0, vbe=0.7, vce=0.2), "active")
        self.assertEqual(classify_region(vbb=1.0, vbe=0.7, vce=0.1999), "saturation")
        self.assertEqual(classify_region(vbb=1.0, vbe=0.7, vce=1.0), "active")


class TestAnalyze(unittest.TestCase):
    def test_reference_is_active_without_warnings(self):
        r = analyze(BiasInputs(**VALID))
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())
        self.assertIsNone(r.ic_sat)
        self.assertAlmostEqual(r.ic, 1.323675e-3, delta=1e-8)
        self.assertAlmostEqual(r.vbb, 2.1052632, delta=1e-6)
        self.assertAlmostEqual(r.rb, 8245.614, delta=1e-2)
        self.assertLess(r.max_rel_diff, 1e-9)
        self.assertAlmostEqual(r.ic_thevenin, r.ic_nodal, delta=1e-12)

    def test_cutoff(self):
        r = analyze(BiasInputs(**{**VALID, "r2": 1000.0}))
        self.assertEqual(r.region, "cutoff")
        self.assertEqual((r.ib, r.ic, r.ie), (0.0, 0.0, 0.0))
        self.assertAlmostEqual(r.vce, 12.0)
        self.assertAlmostEqual(r.vc, 12.0)
        self.assertAlmostEqual(r.vb, 0.25)
        self.assertAlmostEqual(r.ve, 0.0)
        self.assertIn("ตัดการทำงาน", r.warnings[0])

    def test_saturation_is_reported_not_clamped(self):
        r = analyze(BiasInputs(**{**VALID, "rc": 47000.0}))
        self.assertEqual(r.region, "saturation")
        self.assertAlmostEqual(r.ic, 1.323675e-3, delta=1e-8)      # extrapolated, not clamped
        self.assertLess(r.vce, VCE_SAT_V)
        self.assertAlmostEqual(r.ic_sat, 0.2458333e-3, delta=1e-8)
        self.assertIn("อิ่มตัว", r.warnings[0])

    def test_low_headroom_warns_but_stays_active(self):
        r = analyze(BiasInputs(**{**VALID, "r1": 70000.0, "re": 100.0}))
        self.assertEqual(r.region, "active")
        self.assertAlmostEqual(r.vce, 0.4245, delta=1e-3)
        self.assertEqual(len(r.warnings), 1)
        self.assertIn("headroom", r.warnings[0])

    def test_huge_but_finite_resistance_returns_cutoff(self):
        r = analyze(BiasInputs(**{**VALID, "r1": 1e308}))
        self.assertEqual(r.region, "cutoff")
```

- [ ] **Step 2: Run it and watch it fail** → `ImportError`.

- [ ] **Step 3: Implement**

`classify_region` returns `"cutoff"` when `vbb <= vbe`, else `"saturation"` when `vce < VCE_SAT_V`, else `"active"`. `analyze` calls `validate`, computes `(vbb, rb)`, and on cutoff returns a `BiasResult` with zero currents, `ve=0`, `vb=vbb`, `vc=VCC`, `vce=VCC`, `ic_thevenin=ic_nodal=0.0`, `max_rel_diff=0.0`, `ic_sat=None`, and one Thai warning containing `"ทรานซิสเตอร์ตัดการทำงาน"`. Otherwise it runs both solvers, `relative_difference`, and `classify_region`, and sets `ic_sat = (vcc - VCE_SAT_V) / (rc + re)` only for saturation. Warnings: saturation → one message containing `"อิ่มตัว"`; active with `vce < 1.0` → one message containing `"headroom"`.

- [ ] **Step 4: Run it and watch it pass** → `python -m unittest test_bjt -v`, all OK.

- [ ] **Step 5: Commit** `feat: add region classification and bias analysis`

---

### Task 5: Stiff-divider approximation

**Files:**
- Modify: `bjt.py`
- Test: `test_bjt.py`

**Interfaces:**
- Consumes: `analyze`, `BiasResult`.
- Produces: three new `BiasResult` fields — `ic_approx: float | None`, `approx_error_pct: float | None`, `stiff_divider: bool | None`, all `None` unless the region is `"active"`.

- [ ] **Step 1: Write the failing test**

```python
class TestApproximation(unittest.TestCase):
    def test_reference_approximation(self):
        r = analyze(BiasInputs(**VALID))
        self.assertAlmostEqual(r.ic_approx, 1.4052632e-3, delta=1e-9)
        self.assertAlmostEqual(r.approx_error_pct, 6.1638, delta=0.01)
        self.assertTrue(r.stiff_divider)

    def test_non_stiff_divider_is_flagged(self):
        r = analyze(BiasInputs(vcc=12.0, r1=1000.0, r2=10000.0,
                               rc=10.0, re=10.0, beta=10.0, vbe=0.7))
        self.assertEqual(r.region, "active")
        self.assertFalse(r.stiff_divider)
        self.assertAlmostEqual(r.ic_approx, 1.0209, delta=1e-3)
        self.assertGreater(r.approx_error_pct, 300.0)

    def test_not_offered_outside_the_active_region(self):
        for fixture in ({**VALID, "r2": 1000.0}, {**VALID, "rc": 47000.0}):
            with self.subTest(fixture=fixture):
                r = analyze(BiasInputs(**fixture))
                self.assertIsNone(r.ic_approx)
                self.assertIsNone(r.approx_error_pct)
                self.assertIsNone(r.stiff_divider)
```

- [ ] **Step 2: Run it and watch it fail** → `AttributeError: 'BiasResult' object has no attribute 'ic_approx'`.

- [ ] **Step 3: Implement** `IC_approx = (VBB - VBE) / RE`, `error_pct = (IC_approx - IC)/IC * 100`, `stiff = beta * RE >= 10 * RB`, all only for `region == "active"`; `None` otherwise. Add the constant `STIFF_FACTOR = 10`.

- [ ] **Step 4: Run it and watch it pass** → `python -m unittest test_bjt -v`, all OK.

- [ ] **Step 5: Commit** `feat: add stiff-divider approximation comparison`

---

### Task 6: Unit formatting

**Files:**
- Modify: `bjt.py`
- Test: `test_bjt.py`

**Interfaces:**
- Produces: `bjt.format_current(amperes: float) -> str`, `bjt.format_voltage(volts: float) -> str`, `bjt.format_resistance(ohms: float) -> str`. Zero renders as `0 A`, `0 V`, `0 Ω`.

- [ ] **Step 1: Write the failing test**

```python
from bjt import format_current, format_resistance, format_voltage


class TestFormatting(unittest.TestCase):
    def test_currents(self):
        cases = ((1.323675e-3, "1.32 mA"), (8.8245e-6, "8.82 µA"), (2.0, "2.00 A"),
                 (0.5, "500 mA"), (1e-9, "1.00 nA"), (0.0, "0 A"))
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(format_current(value), expected)

    def test_voltages(self):
        cases = ((7.755425, "7.76 V"), (0.4245, "424 mV"), (5e-4, "500 µV"),
                 (1200.0, "1.20 kV"), (0.0, "0 V"))
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(format_voltage(value), expected)

    def test_resistances(self):
        cases = ((8245.614, "8.25 kΩ"), (470.0, "470 Ω"), (2.2e6, "2.20 MΩ"), (0.0, "0 Ω"))
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(format_resistance(value), expected)
```

- [ ] **Step 2: Run it and watch it fail** → `ImportError`.

- [ ] **Step 3: Implement** each as: pick the unit band by `abs(value)` (`< 1e-6` nA, `< 1e-3` µA, `< 1` mA, else A for current; `< 1e-3` µV, `< 1` mV, `< 1e3` V, else kV for voltage; `< 1e3` Ω, `< 1e6` kΩ, else MΩ for resistance), scale, and render `f"{format(scaled, '#.3g')} {unit}"`. Return early for `value == 0`.

- [ ] **Step 4: Run it and watch it pass** → `python -m unittest test_bjt -v`, all OK.

- [ ] **Step 5: Commit** `feat: add SI unit formatting`

---

### Task 7: Form parsing and the GET page

**Files:**
- Create: `app.py`, `templates/index.html`, `requirements.txt`
- Test: `test_app.py`

**Interfaces:**
- Consumes: `BiasInputs`.
- Produces: `app.app` (the Flask application), `app.parse_number(text: str) -> float`, `app.parse_resistance(text: str) -> float`, `app.build_inputs(form: dict) -> BiasInputs`, route `GET /`.

- [ ] **Step 1: Write the failing test**

```python
import unittest
from app import app, parse_number, parse_resistance


class TestParsing(unittest.TestCase):
    def test_plain_numbers(self):
        self.assertAlmostEqual(parse_number("12"), 12.0)
        self.assertAlmostEqual(parse_number(" 0.7 "), 0.7)

    def test_resistance_suffixes(self):
        cases = (("47k", 47000.0), ("4.7k", 4700.0), ("1M", 1e6),
                 ("47kΩ", 47000.0), ("47kohm", 47000.0), ("1000", 1000.0))
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_resistance(text), expected)

    def test_rejects_expressions_and_separators(self):
        for text in ("4.7*1000", "47,000", "", "abc", "47kk"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_resistance(text)


class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_renders_form(self):
        resp = self.client.get("/")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("VCC", body)
        self.assertIn('name="r1"', body)
        self.assertIn('value="47k"', body)
```

- [ ] **Step 2: Run it and watch it fail** → `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Install Flask and implement**

`python -m pip install "flask>=3.0,<4"`, then write `requirements.txt` with `flask>=3.0,<4`.

`parse_number`: strip whitespace, reject empty, accept only a plain decimal literal (no `*`, `,`, or unit characters) via `float()`, raising `ValueError("กรุณากรอกเป็นตัวเลข")` on failure. `parse_resistance`: also accept a trailing `k`/`K` (×1e3), `M` (×1e6), and optional `Ω`/`ohm`, matching `^([0-9]*\.?[0-9]+)\s*([kKM])?\s*(Ω|ohm)?$`; anything else raises the same Thai message. `build_inputs` reads keys `vcc, r1, r2, rc, re, beta, vbe` from the form, parses resistances with `parse_resistance` and the rest with `parse_number`, and returns `BiasInputs`.

`templates/index.html`: one page, form with `method="post"`, seven labelled inputs, each `value="{{ raw.vcc }}"` etc., a submit button, `<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`, and a placeholder results block. Defaults for `GET` (module constant `DEFAULTS`): `12`, `47k`, `10k`, `2.2k`, `1k`, `150`, `0.7`.

- [ ] **Step 4: Run it and watch it pass** → `python -m unittest test_app -v`, all OK.

- [ ] **Step 5: Commit** `feat: add Flask form and input parsing`

---

### Task 8: POST, results, warnings and CSS

**Files:**
- Modify: `app.py`, `templates/index.html`
- Create: `static/style.css`
- Test: `test_app.py`

**Interfaces:**
- Consumes: `parse_*`, `build_inputs`, `bjt.analyze`, all three formatters.
- Produces: `POST /` rendering the Q-point or a Thai error, badged region, warnings, and the comparison table; `static/style.css`.

- [ ] **Step 1: Write the failing test**

```python
FORM = {"vcc": "12", "r1": "47k", "r2": "10k", "rc": "2.2k",
        "re": "1k", "beta": "150", "vbe": "0.7"}


class TestResults(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_reference_qpoint(self):
        resp = self.client.post("/", data=FORM)
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("1.32 mA", body)
        self.assertIn("7.76 V", body)
        self.assertIn("Active", body)
        self.assertIn("1.41 mA", body)      # IC_approx
        self.assertIn("6.16", body)          # error %

    def test_invalid_input_is_readable_and_keeps_typed_value(self):
        resp = self.client.post("/", data={**FORM, "r1": "0"})
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ต้องมากกว่า 0", body)
        self.assertIn('value="0"', body)
        self.assertNotIn("Traceback", body)

    def test_non_numeric_input(self):
        resp = self.client.post("/", data={**FORM, "vcc": "abc"})
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("กรุณากรอกเป็นตัวเลข", body)

    def test_saturation_warning(self):
        resp = self.client.post("/", data={**FORM, "rc": "47k"})
        body = resp.get_data(as_text=True)
        self.assertIn("Saturation", body)
        self.assertIn("246 µA", body)

    def test_cutoff_warning_and_dash_in_comparison(self):
        resp = self.client.post("/", data={**FORM, "r2": "1k"})
        body = resp.get_data(as_text=True)
        self.assertIn("Cutoff", body)
        self.assertIn("—", body)
```

- [ ] **Step 2: Run it and watch it fail** → `POST /` returns 405, assertions fail.

- [ ] **Step 3: Implement** the route and template

`GET /` renders with `DEFAULTS`; `POST /` parses, and on `ValueError` renders the same page with the messages in an error block, `result=None`, and `raw` set to the submitted values. On success renders `result` with: a badge whose text is the capitalised region (`Active` / `Cutoff` / `Saturation`), the eight quantities through the formatters, the intermediate `VBB`/`RB`, each warning as a list item, and a comparison table with `IC` from Thévenin, `IC` from nodal, `max_rel_diff` in `{:.1e}` form, and — only when `ic_approx` is not `None` — `IC_approx`, `approx_error_pct` to 2 decimals, and `stiff ✓` / `stiff ✗`. When `ic_approx` is `None` that row shows `—` with the text `ไม่มีผล (Q-point ไม่อยู่ในโหมดแอกทีฟ)`. `static/style.css`: plain readable form grid, monospace numbers, a colour per region badge, and error/warning blocks. No JavaScript.

- [ ] **Step 4: Run it and watch it pass** → `python -m unittest test_app -v`, all OK.

- [ ] **Step 5: Commit** `feat: render bias results, warnings and comparison`

---

### Task 9: README, full suite, live demo, push

**Files:**
- Modify: `README.md`
- Test: whole suite + a real HTTP request

**Interfaces:**
- Produces: the committed, pushed branch and a screenshot-free proof the server answers.

- [ ] **Step 1: Add the README section** describing the ENG29 2121 app: install (`python -m pip install -r requirements.txt`), run (`python app.py`), open `http://127.0.0.1:5000`, the input units, the two methods and why they agree, and `python -m unittest -v`. Keep the existing Compro section intact.

- [ ] **Step 2: Run the whole suite**

Run: `python -m unittest -v` → all tests from `test_electrical.py`, `test_bjt.py`, `test_app.py` pass.

- [ ] **Step 3: Start the server and hit it**

```powershell
Start-Process python -ArgumentList "app.py"
Start-Sleep -Seconds 3
(Invoke-WebRequest http://127.0.0.1:5000).StatusCode
```

Expected: `200`. Then POST the reference fixture with `Invoke-WebRequest -Method POST -Body @{...}` and confirm the response contains `1.32 mA`.

- [ ] **Step 4: Commit**

```powershell
git add README.md
git commit -m "docs: document the BJT bias web app"
```

- [ ] **Step 5: Push**

```powershell
git push origin main
```

Expected: `main -> main`. Verify with `git status -sb` → `## main...origin/main` and no ahead marker.

---

## Self-Review

**Spec coverage:** every spec section maps to a task — validation (1), both solvers (2, 3), agreement (3, 4), cutoff gate and region rules (4), approximation (5), units (6), Flask layer, one page and CSS (7, 8), acceptance criteria 1–6 (9). Non-goals need no task.

**Step scan:** each step is one action with one checkable result; only Gaussian elimination and the spec's equations carry bodies, because the tests do not determine them.

**Type consistency:** `BiasInputs` field names, the seven solver keys, `BiasResult` field names and the `None` sentinels match across tasks 1–8; formatter names are used identically in tasks 6 and 8.

**Review Focus:** beta floor and `RE = 0` (task 1), non-finite input (task 1) and huge finite input (task 4), region boundaries (task 4), and typed input forms (task 7) each have a test in the owning task.

**Proportion:** the plan is longer than the spec only because it carries the tests; no task transcribes a full module.
