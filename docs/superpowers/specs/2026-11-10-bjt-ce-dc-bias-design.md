# BJT Common-Emitter DC Bias Web App — Design

Course: ENG29 2121 · Date: 2026-11-10 · Status: awaiting approval

## Intent and why

Students need to find the DC operating point (Q-point) of a voltage-divider-biased
common-emitter stage and be told when the transistor is not in the active region.
Doing it by hand hides arithmetic mistakes; a small web app shows the numbers with
units and cross-checks them against a second, independently derived calculation.
The lab is short, so the app must stay small enough to read and grade in one sitting.

## What it is

A single-page Flask app. The student enters seven values, gets the Q-point back with
units, input validation, region warnings, and a table proving two different
derivations agree.

Inputs: `VCC, R1, R2, RC, RE, beta, VBE`

Outputs: `IB, IC, IE, VB, VE, VC, VCE`, the region (cutoff / active / saturation),
warnings, intermediate values `VBB` and `RB`, and the comparison table.

## Goals

- Correct DC analysis of the voltage-divider bias circuit, with base-current loading.
- Separate engineering module (`bjt.py`) that never imports Flask, fully testable.
- Visible, honest validation — bad input never produces a 500 or a silent zero.
- A Q-point that is cross-checked by a second derivation, with the difference shown.
- Runs on localhost from a clean checkout on Windows with one `pip install`.

## Non-goals

- No AC small-signal analysis, gain, frequency response, or transient simulation.
- No schematic editor, no netlist, no multi-transistor circuits, no FETs, no op-amps.
- No database, no accounts, no sessions, no JavaScript, no plotting.
- Not a general circuit solver: this one topology only.

## Anti-goals (fails even if it works)

- Two "independent" methods that share code, so the agreement check proves nothing.
- Silently clamping a saturated Q-point to a valid-looking number.
- Validation that raises a traceback page instead of a readable message.
- Copy-pasted formulas with no test pinning them to a hand calculation.

## Constraints

- Python 3.12.7, Flask installed from PyPI (only external dependency), `pip 24.2`.
- `git` is not on PATH: call `C:\Users\B6807757\AppData\Local\Programs\Git\cmd\git.exe`.
- Remote `origin` = `https://github.com/B6807757/Gitlab.git`, branch `main`, currently
  clean and level with `origin/main`.
- No git identity configured; use repo-local `Poom <poomhirun2549@gmail.com>`.
- Repo stays flat, like the existing Compro lab: new files live at the repo root.
- UI copy in Thai; technical symbols stay Latin (`VCC`, `IC`, `VCE`).

## Approaches considered

**Independent-calculation structure.** The requirement "compare with an independent
engineering calculation" could mean (A) two derivations of the same physics,
(B) exact vs. the textbook stiff-divider approximation, or (C) both. Chosen: **C**.
A proves the algebra is right; B shows the size of the error students are taught to
ignore. They serve different purposes, so both go in the comparison panel.

**Web layer.** Server-rendered single page, `GET`/`POST` on `/`, no JavaScript.
Rejected: JSON API + client-side fetch (adds a second language and untested client
code for no lab benefit), and a separate results page via redirect (either loses the
entered values on error or needs sessions).

**Math module shape.** Pure functions over a frozen dataclass of inputs, returning a
frozen result dataclass. Rejected: a `BiasCircuit` class with mutation (state buys
nothing here and complicates tests).

## The engineering

Fixed constant `VCE_SAT = 0.2 V`, documented in the module.

### Method A — Thévenin closed form

```
VBB = VCC * R2 / (R1 + R2)
RB  = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (1 + beta) * RE)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE
VC  = VCC - IC * RC
VB  = VE + VBE
VCE = VC - VE
```

### Method B — nodal linear system

Unknowns `[VB, VC, IC]`; assumes `VBE` is the given constant and `beta` is constant:

```
1) base:      (VB - VCC)/R1 + VB/R2 + IC/beta        = 0
2) collector: (VCC - VC)/RC - IC                     = 0
3) emitter:   (VB - VBE)/RE - ((beta+1)/beta) * IC   = 0
```

Solved with Gaussian elimination and partial pivoting, pure Python, no NumPy.
`VE = VB - VBE`, `VCE = VC - VE`. Method B shares no algebra with Method A.

### Gate both methods: cutoff

`VBB <= VBE` means the base-emitter junction never turns on, so both methods return
the defined cutoff result instead of solving: `IB = IC = IE = 0`, `VE = 0`,
`VB = VBB`, `VC = VCC`, `VCE = VCC`, region = cutoff. This is a physical prerequisite
applied before either derivation, not part of either derivation.

### Agreement

Max relative difference over `{IB, IC, IE, VB, VC, VE, VCE}`, denominator
`max(|A|, 1e-12)`. Displayed in the comparison panel. Unit test requires `< 1e-9`;
the UI flags a failure above `1e-6`.

### Method C — stiff-divider approximation

```
IC_approx = (VBB - VBE) / RE
error_pct = (IC_approx - IC) / IC * 100
stiff     = (beta * RE) >= 10 * RB          # textbook rule of thumb
```

Shown next to the exact `IC` so the student sees what ignoring base current costs.

### Region rules

| Condition | Region | Message |
|---|---|---|
| `VBB <= VBE` | cutoff | transistor off, `VCE = VCC` |
| `VCE < 0.2` | saturation | Q-point invalid; also show `IC_sat = (VCC - 0.2)/(RC + RE)` |
| `0.2 <= VCE < 1.0` | active, warned | low headroom, close to saturation |
| `VCE >= 1.0` | active | normal |

A saturated result is never clamped. The active-region numbers are reported as
computed, with a clear warning that they are not the real operating point.

### Validation (raises `ValueError` with a Thai message)

- all seven values must be finite numbers (parse failures handled at the Flask layer)
- `VCC > 0`, `R1 > 0`, `R2 > 0`, `RC > 0`, `RE > 0`
- `beta >= 1`
- `0 <= VBE < VCC`

### Units and formatting

Auto-scaled SI display, 3 significant digits: current in nA / µA / mA / A, voltage
in µV / mV / V / kV, resistance in Ω / kΩ / MΩ. Values outside those ranges fall
back to scientific notation. Pure formatting functions in `bjt.py`, unit-tested.

*Builder call:* 3 significant figures is authoritative for everything the page
shows. The reference fixture's longer decimals are the expected engineering values,
asserted with `assertAlmostEqual` / relative tolerance — not the display strings.

### Comparison panel in non-active regions

*Builder call:* when the region is not active, the Method C row and the A/B
agreement row show `—` with the reason "ไม่มีผล (Q-point ไม่อยู่ในโหมดแอกทีฟ)"
instead of a percentage. Dividing by `IC = 0` in cutoff would raise
`ZeroDivisionError`, and a percentage of a saturated, extrapolated `IC` is
physically misleading. This is one branch on `region != active`; the result object
carries `None` for `ic_approx` and `error_pct` there.

### Input parsing

*Builder call:* plain decimal numbers; surrounding whitespace ignored. Resistance
fields additionally accept a `k` / `K` / `M` suffix (`47k`, `4.7k`, `1M`) and an
optional `Ω` / `ohm`, because students copy values straight off the lab sheet.
Thousands separators and expression syntax (`4.7*1000`) are rejected with a Thai
message. Everything else is a parse error handled by the Flask layer.

## Files

```
bjt.py                     engineering logic, dataclasses, validation, formatting
app.py                     Flask app and routes
templates/index.html       the one page
static/style.css           styling
test_bjt.py                logic, validation, formatting, region, cross-check
test_app.py                routes via the Flask test client
requirements.txt           flask
README.md                  new ENG29 2121 section
docs/superpowers/specs/2026-11-10-bjt-ce-dc-bias-design.md
```

Existing `electrical.py` / `test_electrical.py` stay untouched; `python -m unittest -v`
at the root runs both labs' tests.

## Reference fixture (pins the tests to a hand calculation)

`VCC=12, R1=47000, R2=10000, RC=2200, RE=1000, beta=150, VBE=0.7` →

```
VBB = 2.105263 V      RB = 8245.614 Ω
IB  = 8.824 µA        IC = 1.3237 mA      IE = 1.3325 mA
VB  = 2.0325 V        VE = 1.3325 V       VC = 9.0879 V
VCE = 7.7554 V        region = active, no warnings
IC_approx = 1.4053 mA → error 6.16 % (stiff rule passes: 150000 >= 82456)
```

Other fixtures: `R2=1000` → cutoff (`VBB = 0.25 V`); `RC=47000` → saturation
(`IC_sat = 0.2458 mA`); `R1=70000, RE=100, RC=2200` → active with low-headroom
warning (`VCE ≈ 0.43 V`).

## Acceptance criteria

1. `python -m unittest -v` green, including the untouched `test_electrical.py`.
2. `python app.py` serves `http://127.0.0.1:5000`; the reference fixture renders the
   values above at 3 significant figures with units and an "active" badge.
3. The comparison panel shows Thévenin, nodal, their max relative difference, plus
   `IC_approx` and its error.
4. Bad input (zero resistor, `beta=0`, non-numeric) renders a Thai error message and
   keeps what the student typed; no traceback, no 500.
5. Saturation and cutoff produce distinct, readable warnings.
6. One commit (or a few logical ones) on `main`, pushed to `origin`.

## Left to the builder

- Exact CSS, page layout, and Thai wording of labels and warnings.
- Whether results appear below the form on the same page (assumed) or as a separate view.
- Default form values (assumed: the reference fixture, since it matches the lab sheet).
- Whether `app.py` exposes a factory; the module-level `app` is sufficient here.
